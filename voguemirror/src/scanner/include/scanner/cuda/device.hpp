#ifndef VM_SCANNER_CUDA_DEVICE_HPP
#define VM_SCANNER_CUDA_DEVICE_HPP

#include <scanner/cuda/internal.hpp>
#include <scanner/cuda/temp_utils.hpp>

////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// TsdfVolume

//__vm_device__
//vm::scanner::device::TsdfVolume::TsdfVolume(elem_type* _data, int3 _dims, float3 _voxel_size, float _trunc_dist, int _max_weight)
//  : data(_data), dims(_dims), voxel_size(_voxel_size), trunc_dist(_trunc_dist), max_weight(_max_weight) {}

//__vm_device__
//vm::scanner::device::TsdfVolume::TsdfVolume(const TsdfVolume& other)
//  : data(other.data), dims(other.dims), voxel_size(other.voxel_size), trunc_dist(other.trunc_dist), max_weight(other.max_weight) {}

__vm_device__ vm::scanner::device::TsdfVolume::elem_type* vm::scanner::device::TsdfVolume::operator()(int x, int y, int z)
{ return data + x + y*dims.x + z*dims.y*dims.x; }

__vm_device__ const vm::scanner::device::TsdfVolume::elem_type* vm::scanner::device::TsdfVolume::operator() (int x, int y, int z) const
{ return data + x + y*dims.x + z*dims.y*dims.x; }

__vm_device__ vm::scanner::device::TsdfVolume::elem_type* vm::scanner::device::TsdfVolume::beg(int x, int y) const
{ return data + x + dims.x * y; }

__vm_device__ vm::scanner::device::TsdfVolume::elem_type* vm::scanner::device::TsdfVolume::zstep(elem_type *const ptr) const
{ return ptr + dims.x * dims.y; }

////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// Projector

__vm_device__ float2 vm::scanner::device::Projector::operator()(const float3& p) const
{
    float2 coo;
    coo.x = __fmaf_rn(f.x, __fdividef(p.x, p.z), c.x);
    coo.y = __fmaf_rn(f.y, __fdividef(p.y, p.z), c.y);
    return coo;
}

////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// Reprojector

__vm_device__ float3 vm::scanner::device::Reprojector::operator()(int u, int v, float z) const
{
    float x = z * (u - c.x) * finv.x;
    float y = z * (v - c.y) * finv.y;
    return make_float3(x, y, z);
}

////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// packing/unpacking tsdf volume element

__vm_device__ ushort2 vm::scanner::device::pack_tsdf (float tsdf, int weight)
{ return make_ushort2 (__float2half_rn (tsdf), weight); }

__vm_device__ ushort4 vm::scanner::device::pack_tsdf(float tsdf, int weight, ushort rg, ushort ba)
{
  return make_ushort4(__float2half_rn(tsdf), weight, rg, ba);
}

__vm_device__ float vm::scanner::device::unpack_tsdf(ushort4 value, int& weight, ushort& rg, ushort& ba)
{
    weight = value.y;
    rg = value.z;
    ba = value.w;

    return __half2float (value.x);
}
__vm_device__ float vm::scanner::device::unpack_tsdf (ushort4 value) { return __half2float (value.x); }


__vm_device__ ushort2 vm::scanner::device::rgba2ushort(uchar4 color)
{
  ushort2 tmp;
  tmp.x = color.x * 256 + color.y;  // r and g
  tmp.y = color.z * 256 + color.w;  // b and a

  return tmp;
}
      
__vm_device__ uchar4 vm::scanner::device::ushort2rgba(ushort2 color)
{
  uchar4 tmp;

  tmp.w = color.y % 256; color.y /= 256;  // w
  tmp.z = color.y % 256;  // b
  tmp.y = color.x % 256; color.x /= 256; // g
  tmp.x = color.x % 256;  // r

  return tmp;
}

////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// Utility

namespace vm
{
	namespace scanner
	{
    namespace device
    {
      __vm_device__ Vec3f operator*(const Mat3f& m, const Vec3f& v)
      { return make_float3(dot(m.data[0], v), dot (m.data[1], v), dot (m.data[2], v)); }

      __vm_device__ Vec3f operator*(const Aff3f& a, const Vec3f& v) { return a.R * v + a.t; }

      __vm_device__ Vec3f tr(const float4& v) { return make_float3(v.x, v.y, v.z); }

      struct plus
      {
        __vm_device__ float operator () (float l, float r) const  { return l + r; }
        __vm_device__ double operator () (double l, double r) const  { return l + r; }
      };

      struct gmem
      {
        template<typename T> __vm_device__ static T LdCs(T *ptr);
        template<typename T> __vm_device__ static void StCs(const T& val, T *ptr);
      };

      template<> __vm_device__ ushort2 gmem::LdCs(ushort2* ptr);
      template<> __vm_device__ void gmem::StCs(const ushort2& val, ushort2* ptr);

      template<> __vm_device__ ushort4 gmem::LdCs(ushort4* ptr);
      template<> __vm_device__ void gmem::StCs(const ushort4& val, ushort4* ptr);
    }
	}
}

#if defined __CUDA_ARCH__ && __CUDA_ARCH__ >= 200

    #if defined(_WIN64) || defined(__LP64__)
        #define _ASM_PTR_ "l"
    #else
        #define _ASM_PTR_ "r"
    #endif

    template<> __vm_device__ ushort2 vm::scanner::device::gmem::LdCs(ushort2* ptr)
    {
        ushort2 val;
        asm("ld.global.cs.v2.u16 {%0, %1}, [%2];" : "=h"(reinterpret_cast<ushort&>(val.x)), "=h"(reinterpret_cast<ushort&>(val.y)) : _ASM_PTR_(ptr));
        return val;
    }

    template<> __vm_device__ ushort4 vm::scanner::device::gmem::LdCs(ushort4* ptr)
    {
      ushort4 val;
      asm("ld.global.cs.v4.u16 {%0, %1, %2, %3}, [%4];" : "=h"(reinterpret_cast<ushort&>(val.x)), "=h"(reinterpret_cast<ushort&>(val.y)), "=h"(reinterpret_cast<ushort&>(val.z)), "=h"(reinterpret_cast<ushort&>(val.w)) : _ASM_PTR_(ptr));
      return val;
    }

    template<> __vm_device__ void vm::scanner::device::gmem::StCs(const ushort2& val, ushort2* ptr)
    {
        short cx = val.x, cy = val.y;
        asm("st.global.cs.v2.u16 [%0], {%1, %2};" : : _ASM_PTR_(ptr), "h"(reinterpret_cast<ushort&>(cx)), "h"(reinterpret_cast<ushort&>(cy)));
    }

    template<> __vm_device__ void vm::scanner::device::gmem::StCs(const ushort4& val, ushort4* ptr)
    {
        short cx = val.x, cy = val.y, cz = val.z, cw = val.w;
        asm("st.global.cs.v4.u16 [%0], {%1, %2, %3, %4};" : : _ASM_PTR_(ptr), "h"(reinterpret_cast<ushort&>(cx)), "h"(reinterpret_cast<ushort&>(cy)), "h"(reinterpret_cast<ushort&>(cz)), "h"(reinterpret_cast<ushort&>(cw)));
    }
    #undef _ASM_PTR_

#else
    template<> __vm_device__ ushort2 vm::scanner::device::gmem::LdCs(ushort2* ptr) { return *ptr; }
    template<> __vm_device__ void vm::scanner::device::gmem::StCs(const ushort2& val, ushort2* ptr) { *ptr = val; }

    template<> __vm_device__ ushort4 vm::scanner::device::gmem::LdCs(ushort4* ptr) { return *ptr; }
    template<> __vm_device__ void vm::scanner::device::gmem::StCs(const ushort4& val, ushort4* ptr) { *ptr = val; }
    
#endif


#endif
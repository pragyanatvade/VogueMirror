#ifndef VM_SCANNER_PRECOMP_HPP
#define VM_SCANNER_PRECOMP_HPP

#include <iostream>

#include <vector_functions.h>

#include <scanner/types.hpp>
#include <scanner/scanner.hpp>
#include <scanner/cuda/internal.hpp>
#include <scanner/cuda/tsdf_volume.hpp>
#include <scanner/cuda/imgproc.hpp>
#include <scanner/cuda/projective_icp.hpp>

namespace vm
{
	namespace scanner
	{
		template<typename D, typename S>
		inline D device_cast(const S& source)
		{
			return *reinterpret_cast<const D*>(source.val);
		}

		template<>
		inline device::Aff3f device_cast<device::Aff3f, Affine3f>(const Affine3f& source)
		{
			device::Aff3f aff;
			Mat3f R = source.rotation();
			Vec3f t = source.translation();
			aff.R = device_cast<device::Mat3f>(R);
			aff.t = device_cast<device::Vec3f>(t);
			return aff;
		}
	}
}

#endif
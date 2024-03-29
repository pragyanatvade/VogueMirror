#include <scanner/precomp.hpp>

using namespace vm::scanner;
using namespace vm::scanner::cuda;

////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// TsdfVolume::Entry

float vm::scanner::cuda::TsdfVolume::Entry::half2float(half)
{ throw "Not implemented"; }

vm::scanner::cuda::TsdfVolume::Entry::half vm::scanner::cuda::TsdfVolume::Entry::float2half(float value)
{ throw "Not implemented"; }

////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// TsdfVolume

vm::scanner::cuda::TsdfVolume::TsdfVolume(const Vec3i& dims) : data_(), trunc_dist_(0.03f), max_weight_(128), dims_(dims),
  size_(Vec3f::all(3.f)), pose_(Affine3f::Identity()), gradient_delta_factor_(0.75f), raycast_step_factor_(0.75f)
{ create(dims_); }

vm::scanner::cuda::TsdfVolume::~TsdfVolume() {}

void vm::scanner::cuda::TsdfVolume::create(const Vec3i& dims)
{
  int voxels_number = dims[0] * dims[1] * dims[2];
  data_.create(voxels_number * sizeof(int) * 2);
  setTruncDist(trunc_dist_);
  clear();
}

Vec3i vm::scanner::cuda::TsdfVolume::getDims() const
{ return dims_; }

Vec3f vm::scanner::cuda::TsdfVolume::getVoxelSize() const
{
  return Vec3f(size_[0]/dims_[0], size_[1]/dims_[1], size_[2]/dims_[2]);
}

const CudaData vm::scanner::cuda::TsdfVolume::data() const { return data_; }
CudaData vm::scanner::cuda::TsdfVolume::data() {  return data_; }

Vec3f vm::scanner::cuda::TsdfVolume::getSize() const { return size_; }
void vm::scanner::cuda::TsdfVolume::setSize(const Vec3f& size)
{ size_ = size; setTruncDist(trunc_dist_); }

float vm::scanner::cuda::TsdfVolume::getTruncDist() const { return trunc_dist_; }

void vm::scanner::cuda::TsdfVolume::setTruncDist(float distance)
{
  Vec3f vsz = getVoxelSize();
  float max_coeff = std::max<float>(std::max<float>(vsz[0], vsz[1]), vsz[2]);
  trunc_dist_ = std::max (distance, 2.1f * max_coeff);
}

int vm::scanner::cuda::TsdfVolume::getMaxWeight() const { return max_weight_; }
void vm::scanner::cuda::TsdfVolume::setMaxWeight(int weight) { max_weight_ = weight; }
Affine3f vm::scanner::cuda::TsdfVolume::getPose() const  { return pose_; }
void vm::scanner::cuda::TsdfVolume::setPose(const Affine3f& pose) { pose_ = pose; }
float vm::scanner::cuda::TsdfVolume::getRaycastStepFactor() const { return raycast_step_factor_; }
void vm::scanner::cuda::TsdfVolume::setRaycastStepFactor(float factor) { raycast_step_factor_ = factor; }
float vm::scanner::cuda::TsdfVolume::getGradientDeltaFactor() const { return gradient_delta_factor_; }
void vm::scanner::cuda::TsdfVolume::setGradientDeltaFactor(float factor) { gradient_delta_factor_ = factor; }
void vm::scanner::cuda::TsdfVolume::swap(CudaData& data) { data_.swap(data); }
void vm::scanner::cuda::TsdfVolume::applyAffine(const Affine3f& affine) { pose_ = affine * pose_; }

void vm::scanner::cuda::TsdfVolume::clear()
{ 
  device::Vec3i dims = device_cast<device::Vec3i>(dims_);
  device::Vec3f vsz  = device_cast<device::Vec3f>(getVoxelSize());

  device::TsdfVolume volume(data_.ptr<ushort4>(), dims, vsz, trunc_dist_, max_weight_);
  device::clear_volume(volume);
}

// void vm::scanner::cuda::TsdfVolume::integrate(const Dists& dists, const Affine3f& camera_pose, const Intr& intr)
// {
//   Affine3f vol2cam = camera_pose.inv() * pose_;

//   device::Projector proj(intr.fx, intr.fy, intr.cx, intr.cy);

//   device::Vec3i dims = device_cast<device::Vec3i>(dims_);
//   device::Vec3f vsz  = device_cast<device::Vec3f>(getVoxelSize());
//   device::Aff3f aff = device_cast<device::Aff3f>(vol2cam);

//   device::TsdfVolume volume(data_.ptr<ushort2>(), dims, vsz, trunc_dist_, max_weight_);
//   device::integrate(dists, volume, aff, proj);
// }

void vm::scanner::cuda::TsdfVolume::integrate(const Dists& dists, const Image& colors, const Affine3f& camera_pose, const Intr& intr)
{
  Affine3f vol2cam = camera_pose.inv() * pose_;

  device::Projector proj(intr.fx, intr.fy, intr.cx, intr.cy);

  device::Vec3i dims = device_cast<device::Vec3i>(dims_);
  device::Vec3f vsz  = device_cast<device::Vec3f>(getVoxelSize());
  device::Aff3f aff = device_cast<device::Aff3f>(vol2cam);
  device::Image& img = (device::Image&)colors;

  device::TsdfVolume volume(data_.ptr<ushort4>(), dims, vsz, trunc_dist_, max_weight_);
  device::integrate(dists, img, volume, aff, proj);
}

void vm::scanner::cuda::TsdfVolume::raycast(const Affine3f& camera_pose, const Intr& intr, Depth& depth, Normals& normals)
{
  DeviceArray2D<device::Normal>& n = (DeviceArray2D<device::Normal>&)normals;

  Affine3f cam2vol = pose_.inv() * camera_pose;

  device::Aff3f aff = device_cast<device::Aff3f>(cam2vol);
  device::Mat3f Rinv = device_cast<device::Mat3f>(cam2vol.rotation().inv(cv::DECOMP_SVD));

  device::Reprojector reproj(intr.fx, intr.fy, intr.cx, intr.cy);

  device::Vec3i dims = device_cast<device::Vec3i>(dims_);
  device::Vec3f vsz  = device_cast<device::Vec3f>(getVoxelSize());

  device::TsdfVolume volume(data_.ptr<ushort4>(), dims, vsz, trunc_dist_, max_weight_);
  device::raycast(volume, aff, Rinv, reproj, depth, n, raycast_step_factor_, gradient_delta_factor_);

}

void vm::scanner::cuda::TsdfVolume::raycast(const Affine3f& camera_pose, const Intr& intr, Cloud& points, Normals& normals)
{
  device::Normals& n = (device::Normals&)normals;
  device::Points& p = (device::Points&)points;

  Affine3f cam2vol = pose_.inv() * camera_pose;

  device::Aff3f aff = device_cast<device::Aff3f>(cam2vol);
  device::Mat3f Rinv = device_cast<device::Mat3f>(cam2vol.rotation().inv(cv::DECOMP_SVD));

  device::Reprojector reproj(intr.fx, intr.fy, intr.cx, intr.cy);

  device::Vec3i dims = device_cast<device::Vec3i>(dims_);
  device::Vec3f vsz  = device_cast<device::Vec3f>(getVoxelSize());

  device::TsdfVolume volume(data_.ptr<ushort4>(), dims, vsz, trunc_dist_, max_weight_);
  device::raycast(volume, aff, Rinv, reproj, p, n, raycast_step_factor_, gradient_delta_factor_);
}

DeviceArray<Point> vm::scanner::cuda::TsdfVolume::fetchCloud(DeviceArray<Point>& cloud_buffer) const
{
  enum { DEFAULT_CLOUD_BUFFER_SIZE = 10 * 1000 * 1000 };

  if (cloud_buffer.empty ())
      cloud_buffer.create (DEFAULT_CLOUD_BUFFER_SIZE);

  DeviceArray<device::Point>& b = (DeviceArray<device::Point>&)cloud_buffer;

  device::Vec3i dims = device_cast<device::Vec3i>(dims_);
  device::Vec3f vsz  = device_cast<device::Vec3f>(getVoxelSize());
  device::Aff3f aff  = device_cast<device::Aff3f>(pose_);

  device::TsdfVolume volume((ushort4*)data_.ptr<ushort4>(), dims, vsz, trunc_dist_, max_weight_);
  size_t size = extractCloud(volume, aff, b);

  return DeviceArray<Point>((Point*)cloud_buffer.ptr(), size);
}

void vm::scanner::cuda::TsdfVolume::fetchNormals(const DeviceArray<Point>& cloud, DeviceArray<Normal>& normals) const
{
  normals.create(cloud.size());
  DeviceArray<device::Point>& c = (DeviceArray<device::Point>&)cloud;

  device::Vec3i dims = device_cast<device::Vec3i>(dims_);
  device::Vec3f vsz  = device_cast<device::Vec3f>(getVoxelSize());
  device::Aff3f aff  = device_cast<device::Aff3f>(pose_);
  device::Mat3f Rinv = device_cast<device::Mat3f>(pose_.rotation().inv(cv::DECOMP_SVD));

  device::TsdfVolume volume((ushort4*)data_.ptr<ushort4>(), dims, vsz, trunc_dist_, max_weight_);
  device::extractNormals(volume, c, aff, Rinv, gradient_delta_factor_, (float4*)normals.ptr());
}

void vm::scanner::cuda::TsdfVolume::fetchTangentColors(const DeviceArray<Point>& cloud, DeviceArray<RGB>& colors) const
{
  colors.create(cloud.size());
  DeviceArray<device::Point>& c = (DeviceArray<device::Point>&)cloud;

  device::Vec3i dims = device_cast<device::Vec3i>(dims_);
  device::Vec3f vsz  = device_cast<device::Vec3f>(getVoxelSize());
  device::Aff3f aff  = device_cast<device::Aff3f>(pose_);
  device::Mat3f Rinv = device_cast<device::Mat3f>(pose_.rotation().inv(cv::DECOMP_SVD));

  device::TsdfVolume volume((ushort4*)data_.ptr<ushort4>(), dims, vsz, trunc_dist_, max_weight_);
  device::extractTangentColors(volume, c, aff, Rinv, gradient_delta_factor_, (uchar4*)colors.ptr());
}

void vm::scanner::cuda::TsdfVolume::fetchVertexColors(const DeviceArray<Point>& cloud, DeviceArray<RGB>& colors) const
{
  colors.create(cloud.size());

  DeviceArray<device::Point>& c = (DeviceArray<device::Point>&)cloud;

  device::Vec3i dims = device_cast<device::Vec3i>(dims_);
  device::Vec3f vsz  = device_cast<device::Vec3f>(getVoxelSize());
  device::Aff3f aff  = device_cast<device::Aff3f>(pose_);
  device::Mat3f Rinv = device_cast<device::Mat3f>(pose_.rotation().inv(cv::DECOMP_SVD));

  device::TsdfVolume volume((ushort4*)data_.ptr<ushort4>(), dims, vsz, trunc_dist_, max_weight_);

  device::extractVertexColors(volume, c, aff, Rinv, gradient_delta_factor_, (uchar4*)colors.ptr());

}
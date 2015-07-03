#ifndef VM_SCANNER_CUDA_IMGPROC_HPP
#define VM_SCANNER_CUDA_IMGPROC_HPP

#include <scanner/types.hpp>

namespace vm
{
	namespace scanner
	{
		namespace cuda
    {
    	void depthBilateralFilter(const Depth& in, Depth& out, int ksz, float sigma_spatial, float sigma_depth);

      void depthTruncation(Depth& depth, float threshold);

      void depthBuildPyramid(const Depth& depth, Depth& pyramid, float sigma_depth);

      void computeNormalsAndMaskDepth(const Intr& intr, Depth& depth, Normals& normals);

      void computePointNormals(const Intr& intr, const Depth& depth, Cloud& points, Normals& normals);

      void computeDists(const Depth& depth, Dists& dists, const Intr& intr);

      void resizeDepthNormals(const Depth& depth, const Normals& normals, Depth& depth_out, Normals& normals_out);

      void resizePointsNormals(const Cloud& points, const Normals& normals, Cloud& points_out, Normals& normals_out);

      void waitAllDefaultStream();

      void renderTangentColors(const Normals& normals, Image& image);

      void renderVertexColors(const Cloud& points, const Normals& normals, const Intr& intr, const Vec3f& light_pose, const DeviceArray2D<RGB>& colors, Image& image);

      void renderImage(const Depth& depth, const Normals& normals, const Intr& intr, const Vec3f& light_pose, Image& image);

      void renderImage(const Cloud& points, const Normals& normals, const Intr& intr, const Vec3f& light_pose, Image& image);

    }
	}
}

#endif
#ifndef VM_SCANNER_CAPTURE_HPP
#define VM_SCANNER_CAPTURE_HPP

#include <string>

#include <opencv2/core/core.hpp>

#include <scanner/scanner.hpp>

namespace vm
{
	namespace scanner
	{
		class OpenNISource
		{
 		public:
 			typedef vm::scanner::PixelRGB RGB24;

 			enum { PROP_OPENNI_REGISTRATION_ON = 104 };

 			OpenNISource();
 			OpenNISource(int device);
 			OpenNISource(const std::string& filename);

 			void open(int device);
 			void open(const std::string& filename);

 			void release();

 			~OpenNISource();

 			bool grab(cv::Mat& depth, cv::Mat& image);

 			//parameters taken from camera/oni
      int shadow_value, no_sample_value;
      float depth_focal_length_VGA;
      float baseline;               // mm
      double pixelSize;             // mm
      unsigned short max_depth;     // mm

      bool setRegistration(bool value = false);

    private:
    	struct Impl;
    	cv::Ptr<Impl> impl_;
    	void getParams();
		};
	}
}

#endif
#include <iostream>
#include <fstream>

#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/viz/vizcore.hpp>

#include <scanner/scanner.hpp>
#include <scanner/capture.hpp>

using namespace vm::scanner;

struct ScannerApp
{
	static void KeyboardCallback(const cv::viz::KeyboardEvent& event, void* pthis)
  {
    ScannerApp& scanner = *static_cast<ScannerApp*>(pthis);

    if(event.action != cv::viz::KeyboardEvent::KEY_DOWN)
      return;

    if(event.code == 't' || event.code == 'T')
      scanner.take_cloud(*scanner.scanner_);

    if(event.code == 'i' || event.code == 'I')
      scanner.iteractive_mode_ = !scanner.iteractive_mode_;

    if(event.code == 's' || event.code =='S')
      scanner.save_mesh(*scanner.scanner_);
  }

  ScannerApp(OpenNISource& source) : exit_ (false),  iteractive_mode_(false), capture_ (source)
  {
    ScannerParams params = ScannerParams::default_params();
    scanner_ = Scanner::Ptr( new Scanner(params) );

    capture_.setRegistration(true);

    cv::viz::WCube cube(cv::Vec3d::all(0), cv::Vec3d(params.volume_size), true, cv::viz::Color::apricot());
    viz.showWidget("cube", cube, params.volume_pose);
    viz.showWidget("coor", cv::viz::WCoordinateSystem(0.1));
    viz.registerKeyboardCallback(KeyboardCallback, this);
  }

  void show_depth(const cv::Mat& depth)
  {
    cv::Mat display;
    //cv::normalize(depth, display, 0, 255, cv::NORM_MINMAX, CV_8U);
    depth.convertTo(display, CV_8U, 255.0/4000);
    cv::imshow("Depth", display);
  }

  void show_raycasted(Scanner& scanner)
  {
    const int mode = 3;
    if (iteractive_mode_)
      scanner.renderImage(view_device_, viz.getViewerPose(), mode);
    else
      scanner.renderImage(view_device_, mode);

    view_host_.create(view_device_.rows(), view_device_.cols(), CV_8UC4);
    view_device_.download(view_host_.ptr<void>(), view_host_.step);
    cv::imshow("Scene", view_host_);
  }

  void take_cloud(Scanner& scanner)
  {
    cuda::DeviceArray<Point> cloud = scanner.tsdf().fetchCloud(cloud_buffer);
    cuda::DeviceArray<Normal> normal;
    cuda::DeviceArray<RGB> color;

    scanner.tsdf().fetchNormals(cloud, normal);
    //scanner.tsdf().fetchTangentColors(cloud, color);
    scanner.tsdf().fetchVertexColors(cloud, color);

    cv::Mat cloud_host(1, (int)cloud.size(), CV_32FC4);
    cv::Mat normal_host(1, (int)normal.size(), CV_32FC4);
    cv::Mat color_host(1, (int)cloud.size(), CV_8UC4);

    cloud.download(cloud_host.ptr<Point>());
    normal.download(normal_host.ptr<Normal>());
    color.download(color_host.ptr<RGB>());

    viz.showWidget("Colored Cloud", cv::viz::WCloud(cloud_host, color_host, normal_host));
  }

  void calc_normals(){
    std::ifstream ply_file_in("model.ply");
    std::string s;
    int vcount;

    while(1){
        ply_file_in >> s;
        if(s.compare("vertex") == 0)
            break;
    }
    
    ply_file_in >> vcount;

    while(1){
        ply_file_in >> s;
        if(s.compare("end_header") == 0)
            break;
    }

    std::ofstream ply_file_out("model_edit.ply");
    ply_file_out << "ply\nformat ascii 1.0\nelement vertex "<< vcount<< "\n";
    ply_file_out << "property float x\nproperty float y\nproperty float z\n";
    ply_file_out << "property float nx\nproperty float ny\nproperty float nz\n";
    ply_file_out << "property uchar red\nproperty uchar green\nproperty uchar blue\n";
    ply_file_out << "element face 0\nproperty list uchar int vertex_indices\n";
    ply_file_out << "end_header\n";

    float x,y,z , nx,ny,nz;
    int r,g,b;
    for(int i = 0; i < vcount ; i++){
      
      ply_file_in >> x >> y >> z >> r >> g >> b;

      nx  = 1.0f - 2.0f*(r/255.0f);
      ny  = 1.0f - 2.0f*(g/255.0f);
      nz  = 1.0f - 2.0f*(b/255.0f);

      ply_file_out <<x<<' '<<y<<' '<<z<<' '<<nx<<' '<<ny<<' '<<nz<<' '<<r<<' '<<g<<' '<<b<<'\n';
    }
    ply_file_out.close();
    ply_file_in.close();

  }

  void combine_mesh(){
    std::ifstream norm_file("model_tangent.ply");
    std::ifstream tex_file("model_color.ply");

    std::ofstream combo_file("model_combo.ply");
      

    std::string s;
    int vcount;

      //Get vcount
    while(1){
      norm_file >> s;
      if(s.compare("vertex") == 0)
        break;
    }

    norm_file >> vcount;

    // End normal file header  
    while(1){
      norm_file >> s;
      if(s.compare("end_header") == 0)
        break;
    }

    //End tex file header
    while(1){
      tex_file >> s;
      if(s.compare("end_header") == 0)
        break;
    }

    //MAke combo file
    
    combo_file << "ply\nformat ascii 1.0\nelement vertex "<< vcount<< "\n";
    combo_file << "property float x\nproperty float y\nproperty float z\n";
    combo_file << "property float nx\nproperty float ny\nproperty float nz\n";
    combo_file << "property uchar red\nproperty uchar green\nproperty uchar blue\n";
    combo_file << "element face 0\nproperty list uchar int vertex_indices\n";
    combo_file << "end_header\n";
    
    float x,y,z , nx,ny,nz;
    int r,g,b;
    int rn,gn,bn;
    for(int i = 0; i < vcount ; i++){
      
      norm_file >> x >> y >> z >> rn >> gn >> bn;
      tex_file >> x >> y >> z >> r >> g >> b;

      nx  = 1.0f - 2.0f*(rn/255.0f);
      ny  = 1.0f - 2.0f*(gn/255.0f);
      nz  = 1.0f - 2.0f*(bn/255.0f);

      combo_file <<x<<' '<<y<<' '<<z<<' '<<nx<<' '<<ny<<' '<<nz<<' '<<r<<' '<<g<<' '<<b<<'\n';
    }

    norm_file.close();
    tex_file.close();
    combo_file.close();   
  }

  void save_mesh(Scanner& scanner)
  {   
    cuda::DeviceArray<Point> cloud = scanner.tsdf().fetchCloud(cloud_buffer);
    cuda::DeviceArray<RGB> tangent_color;
    cuda::DeviceArray<RGB> vertex_color;

    scanner.tsdf().fetchVertexColors(cloud, vertex_color);
    scanner.tsdf().fetchTangentColors(cloud, tangent_color);

    cv::Mat cloud_host(1, (int)cloud.size(), CV_32FC4);
    cv::Mat vertex_color_host(1, (int)vertex_color.size(), CV_8UC4);
    cv::Mat tangent_color_host(1, (int)tangent_color.size(), CV_8UC4);

    cloud.download(cloud_host.ptr<Point>());
    vertex_color.download(vertex_color_host.ptr<RGB>());
    tangent_color.download(tangent_color_host.ptr<RGB>());
    
    cv::viz::writeCloud("model_color.ply", cloud_host, vertex_color_host);
    cv::viz::writeCloud("model_tangent.ply", cloud_host, tangent_color_host);
    combine_mesh();
  }

  bool execute()
  {
    Scanner& scanner = *scanner_;
    cv::Mat depth, image;
    double time_ms = 0;
    bool has_image = false;

    while(!exit_ && !viz.wasStopped())
    {
      bool has_frame = capture_.grab(depth, image);
      if (!has_frame)
        return std::cout << "Can't grab" << std::endl, false;

      cv::cvtColor(image, image, CV_RGB2RGBA);

      depth_device_.upload(depth.data, depth.step, depth.rows, depth.cols);
      image_device_.upload(image.data, image.step, image.rows, image.cols);
      {
        SampledScopeTime fps(time_ms); (void)fps;
        has_image = scanner(depth_device_, image_device_);
      }

      if (has_image)
        show_raycasted(scanner);

      show_depth(depth);
      cv::imshow("Image", image);

      if (!iteractive_mode_)
        viz.setViewerPose(scanner.getCameraPose());

      int key = cv::waitKey(3);

      switch(key)
      {
        case 't': case 'T' : take_cloud(scanner); break;
        case 'i': case 'I' : iteractive_mode_ = !iteractive_mode_; break;
        case 's': case 'S' : save_mesh(scanner); break;
        case 27: case 32: exit_ = true; break;
      }

      //exit_ = exit_ || i > 100;
      viz.spinOnce(3, true);
    }
    return true;
  }

  bool exit_, iteractive_mode_;
  OpenNISource& capture_;
  Scanner::Ptr scanner_;
  cv::viz::Viz3d viz;

  cv::Mat view_host_;
  cuda::Image view_device_;
  cuda::Depth depth_device_;
  cuda::DeviceArray2D<RGB> image_device_;
  cuda::DeviceArray<Point> cloud_buffer;
};

int main (int argc, char** argv)
{
	int device = 0;
  cuda::setDevice (device);
  cuda::printShortCudaDeviceInfo (device);
	
	if(cuda::checkIfPreFermiGPU(device))
    return std::cout << std::endl << "Scanner is not supported for pre-Fermi GPU architectures, and not built for them by default. Exiting..." << std::endl, 1;

  OpenNISource capture;
  
  if(argc == 1)
  {
    capture.open (0);
  }
  else if(argc == 2)
  {
    capture.open (argv[1]);
  }
  else
  {
    std::cout << "Invalid Arguments" << std::endl;
  }

  //capture.open (0);
  //capture.open("/home/pragyan/dataset/burghers.oni");
  //capture.open("/home/pragyan/dataset/copyroom.oni");
  
  ScannerApp app (capture);

  // executing
  try { app.execute (); }
  catch (const std::bad_alloc& /*e*/) { std::cout << "Bad alloc" << std::endl; }
  catch (const std::exception& /*e*/) { std::cout << "Exception" << std::endl; }

	return 0;
}
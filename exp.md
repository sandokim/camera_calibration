### cam0, cam1, cam2, cam3 --> cam2 intrisnics, z축 방향이 반대로 추정되는 이미지가 몇개 있어서 신뢰할 수 없음


난 intrinsics를 이미 구해놓았고 multi로 캡처한 이미지와 이미지 사이에서 extrinsics를 구하고 싶어. 

ret, rvec, tvec = cv.solvePnP(objp, imgpts, mtx, dist)
# The cv::solvePnP() returns the rotation and the translation vectors that transform a 3D point expressed in the object coordinate frame to the camera coordinate frame, using different methods:
# object(checkerboard) frame -> camera frame: T_board_to_cam

✅ 기본 아이디어
각 카메라에서 체커보드를 촬영한 이미지를 이용해, solvePnP를 통해 각 카메라 기준 체커보드의 pose를 구합니다. 즉, 체커보드가 각 카메라 좌표계에서 어디에 있는지를 계산합니다.

SolvePnP로 각 카메라 프레임에서 체커보드의 위치가 계산됨

여기서 한 발 더 나아가면, 역변환을 통해 체커보드 기준에서의 카메라 pose를 얻을 수 있습니다. 예를 들어, 카메라 1 기준에서 체커보드의 pose가 있다면, 그 역행렬을 취하면 체커보드 기준에서 카메라 1의 pose가 됩니다.

이렇게 구한 각 카메라의 pose를 체커보드 좌표계 상에 위치시키면, 서로 다른 카메라들 간의 상대 pose 역시 계산할 수 있습니다. 


object_points가 xy plane으로 정의되서 axes를 그릴떄 파란색 z축만 board_pose에서 이상하게 나와, xy가 right down forward라는 가정하에 xy plane기준 법선 벡터로 정의하면 될거 같은데. 어떻게 하면 될까? camera pose visualize할때 문제가 되는것 같아서
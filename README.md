### 카메라 보정 및 자세 추정 프로세스 

#### 1. 내부 파라미터 보정 (`camera_calibration_intrinsics.py`)
- **실행 빈도:** 카메라 기종당 한 번만 실행
- **목적:** 카메라의 내부 파라미터(초점 거리, 광학 중심 등)를 구함

#### 2. 외부 파라미터 보정 (`camera_calibration_extrinsics.py`)
- **실행 빈도:** 데이터셋 구축 시마다 실행
- **목적:**
  - **데이터 수집:** 체스보드 이미지(`chessboard_extrinsics`)와 RGB 이미지 획득
  - **외부 파라미터 계산:**
    - 체스보드 이미지를 이용하여 외부 파라미터(변환 벡터 `tvecs`, 회전 벡터 `rvecs`) 구함
    - 내부 파라미터를 사용하여 RGB 이미지 왜곡 보정

#### 3. 핸드-아이 보정 (`hand_eye_calibration.py`)
- **목적:**
  - 2단계에서 얻은 외부 파라미터(`tvecs`, `rvecs`)로 `cam2target` 변환 구성
  - RGB 이미지 촬영 상황에 맞춰 일정 각도 간격으로 `world2gripper` 변환 수동 구성
  - `cv2.calibrateHandEye` 함수 사용하여 하나의 `w2c`(월드에서 카메라로) 행렬 계산
  - `w2c`의 inverse를 취하여 `c2w`를 계산

#### 4. 가상 자세 변환 및 JSON 생성 (`transform_json_virtual_poses.py`)
- **목적:**
  - 3단계에서 설정한 월드 좌표계(WCS)와 `c2w` 행렬, 1단계의 내부 파라미터 불러옴
  - WCS 기준으로 `w2g`(월드에서 그리퍼로)와 `g2f`(그리퍼에서 얼굴 좌표로) 변환 정의
  - `c2w`를 통해 `c2f`(카메라에서 얼굴 좌표로) 변환 계산
  - 최종적으로 `f2c`(얼굴 좌표에서 카메라로) 변환을 계산하고, OpenGL 및 Blender 기준인 `right, up, back`으로 축 변경
  - 최종 `f2c` 변환과 RGB 이미지 경로를 JSON 파일 형태로 저장 및 학습/테스트 세트로 분할

### 단계 요약
1. **내부 파라미터 보정:** 카메라 기종당 한 번 실행하여 내부 파라미터 구함
2. **외부 파라미터 보정:** 데이터셋마다 실행하여 외부 파라미터 계산 및 이미지 왜곡 보정
3. **핸드-아이 보정:** `cam2target` 및 `world2gripper` 변환 계산, `c2w` 행렬 구함
4. **변환 및 JSON 생성:** 변환을 계산하여 JSON 파일로 저장, 학습/테스트 세트로 분할

---



# 알려진 3D 점(objpoints) 값과 감지된 코너의 해당 픽셀 좌표(imgpoints) 전달, 카메라 캘리브레이션 수행
ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(
    objpoints, imgpoints, gray.shape[::-1], None, None
)

"""
ret: 양수면 True --> Camera Calibration 성공
mtx: Camera matrix(=Camera Intrinsics); K로 표기
K =[
    [f_x, s, c_x],
    [0, f_y, c_y],
    [0, 0, 1]
]
dist: distortion coefficient
rvecs: 3x1 rotation vector (list contains # of images) --> i.e. len(rvecs)=26 / rvecs[0] 3x1 rotation vector
tvecs: 3x1 translation vector (list contains # of images) --> i.e. len(tvecs)=26 / tvecs[0] 3x1 translation vector

https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html#ga3207604e4b1a1758aa66acb6ed5aa65d
rvecs	Output vector of rotation vectors (Rodrigues ) estimated for each pattern view (e.g. std::vector<cv::Mat>>). That is, each i-th rotation vector together with the corresponding i-th translation vector (see the next output parameter description) brings the calibration pattern from the object coordinate space (in which object points are specified) to the camera coordinate space. In more technical terms, the tuple of the i-th rotation and translation vector performs a change of basis from object coordinate space to camera coordinate space. Due to its duality, this tuple is equivalent to the position of the calibration pattern with respect to the camera coordinate space.
tvecs	Output vector of translation vectors estimated for each pattern view, see parameter describtion above.
"""



### cam0, cam1, cam2, cam3 --> cam2 intrisnics, z축 방향이 반대로 추정되는 이미지가 몇개 있어서 신뢰할 수 없음

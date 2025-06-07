## 커스텀 카메라 보정 및 자세 추정 프로세스 

### 1. 카메라 내부 파라미터 추정 (`camera_calibration_intrinsics.py`)
- **실행 빈도:** 카메라당 한 번만 실행
- **입력:** 카메라당 20장 이상의 체커보드 이미지
- **목적:** 카메라의 내부 파라미터(초점 거리, 광학 중심, 왜곡 계수)를 구함
- **출력:** 각 카메라별로 intrinsics.json 파일 생성

### 2. 카메라 외부파라미터 추정 (`camera_calibration_extrinsics.py`)
- **실행 빈도:** 데이터셋 구축 시마다 실행
- **입력:** 멀티 카메라 세팅에서 동시 촬영된 체커보드 이미지
- **목적:** 공통된 하나의 좌표계에서 카메라 외부 파라미터(카메라 포즈) 추정
- **출력:**
  - PnP 알고리즘을 통해 체커보드 좌표계(world frame)에서 카메라 좌표계(camera frame)로의 변환 행렬 계산
  - cam0를 reference로 삼고 나머지 카메라들의 외부 파라미터 계산
  - extrinsics.json으로 카메라 포즈 저장

### 3. COLMAP 형태의 cameras.txt, images.txt로 저장
- **입력:** intrinsics.json, extrinsics.json
- **목적:** COLMAP 형태의 카메라 파라미터 저장
- **출력:** cameras.txt, images.txt, points3D.txt(empty)

### 4. sparse/0/ 폴더 생성 후 3.에서 출력한 cameras.txt, images.txt, points3D.txt(empty)를 복사
https://colmap.github.io/faq.html#reconstruct-sparse-dense-model-from-known-camera-poses
camera poses
If the camera poses are known and you want to reconstruct a sparse or dense model of the scene, you must first manually construct a sparse model by creating a cameras.txt, points3D.txt, and images.txt under a new folder:

+── path/to/manually/created/sparse/model
│   +── cameras.txt
│   +── images.txt
│   +── points3D.txt
The points3D.txt file should be empty while every other line in the images.txt should also be empty, since the sparse features are computed, as described below. You can refer to this article for more information about the structure of a sparse model.

#### COLMAP에서 Import Model로 sparse/0/ 폴더 선택하였으나 COLMAP Processing > Database management에서 Cameras와 Images가 모두 비어있음

COLMAP은 .txt 파일 기반의 모델을 GUI에서 직접 사용하지 않습니다.

대신 database.db를 직접 구성하거나 변환하여 사용하는 것이 유일한 방법입니다.

GUI/CLI 모두 동일하게 database.db → 모든 이미지, 카메라, feature 정보 사용

The image reader can only take the parameters for a single camera. If you want to specify the parameters for multiple cameras, you would have to modify the SQLite database directly. This should be easy by modifying the scripts/python/database.py script.


[E20250607 18:53:18.532869 25712 sqlite3_utils.h:49] SQLite error [C:\dev\vcpkg\buildtrees\colmap\src\91af0d6c68-f38268f305.clean\src\colmap\scene\database.cc, line 1114]: SQL logic error

COLMAP GUI에서 발생하는 SQL logic error의 원인은 대부분 database.db의 내부 구조가 COLMAP이 기대하는 형태와 불일치하기 때문입니다. 특히, 다음과 같은 경우에 이 문제가 발생할 수 있습니다:

✅ 원인 요약
images 테이블에서 name 필드와 실제 이미지 파일이 일치하지 않음

예: cam01.jpg로 DB에 저장했지만 images/cam01.jpg 파일이 존재하지 않음

keypoints, descriptors, matches 등의 필수 테이블이 비어 있음

COLMAP GUI는 keypoints 또는 descriptors가 없는 이미지를 열 때 크래시 발생 가능

image_id/camera_id 순번 불일치

수동으로 image_id를 지정하면 AUTOINCREMENT 설정과 충돌

SQLITE 스키마 자체가 COLMAP이 기대하는 것과 다름

NOT NULL 필드에 NULL이 들어갔거나, blob 형식이 잘못됨



#### Question: How to format cameras.txt for Reconstruct sparse/dense model from known camera poses #428 
https://github.com/colmap/colmap/issues/428


### 5. COLMAP points3D.txt를 위한 cameras.txt, images.txt 활용 및 sparse 3D 모델 생성
- **입력:** cameras.txt, images.txt, 체커보드를 촬영한 멀티 카메라 세팅에서 촬영된 이미지
- **목적:** COLMAP을 통한 3D 모델 생성
- **출력:** points3D.txt




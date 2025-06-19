## 커스텀 카메라 보정 및 자세 추정 프로세스 

### 1. 카메라 내부 파라미터 추정 (`camera_calibration_intrinsics.py`)
- **실행 빈도:** 카메라당 한 번만 실행
- **입력:** 카메라당 20장 이상의 체커보드 이미지
- **목적:** 카메라의 내부 파라미터(초점 거리, 광학 중심, 왜곡 계수)를 구함
- **출력:** 각 카메라별로 intrinsics.json 파일 생성

### 2. 카메라 외부파라미터 추정 (`camera_calibration_extrinsics.py`)
- **실행 빈도:** 데이터셋 구축 시마다 실행
- **입력:** 멀티 카메라 세팅에서 동시 촬영된 체커보드 이미지 최소 20장 이상
- **목적:** 공통된 하나의 좌표계에서 카메라 외부 파라미터(카메라 포즈) 추정
- **출력:**
  - PnP 알고리즘을 통해 체커보드 좌표계(world frame)에서 카메라 좌표계(camera frame)로의 변환 행렬 계산
  - cam0를 reference로 삼고 나머지 카메라들의 외부 파라미터 계산
  - extrinsics.json으로 카메라 포즈 저장 

checkerboard로 구한 extrinsics와 intrinsics를 다음과 같이 복사하고,
scene/face/images/camX에 들어있는 image의 이름을 extrinsics.json에 맞게 수정

```python
+── scene/myface/images


+── scene/myface
│   +── extrinsics.json
│   +── images
│   │   +── cam0
│   │   │   +── cam0_img0.jpg
│   │   │   +── intrinsics.json
│   │   +── cam1
│   │   │   +── cam1_img0.jpg
│   │   │   +── intrinsics.json
│   │   +── cam2
│   │   │   +── cam2_img0.jpg
│   │   │   +── intrinsics.json
│   │   +── cam3
│   │   │   +── cam3_img0.jpg
│   │   │   +── intrinsics.json

+── scene/4_camera_calib_data
│   +── checkerboard
│   │   +── cam0
│   │   │   +── cam0_checkerboard_img0.jpg
│   │   │   +── cam0_checkerboard_img1.jpg
│   │   │   +── cam0_checkerboard_img2.jpg
│   │   │   ...
│   │   │   +── intrinsics.json
│   │   +── cam1
│   │   │   +── cam1_checkerboard_img0.jpg
│   │   │   +── cam1_checkerboard_img1.jpg
│   │   │   +── cam1_checkerboard_img2.jpg
│   │   │   ...
│   │   │   +── intrinsics.json
│   │   +── cam2
│   │   │   +── cam2_checkerboard_img0.jpg
│   │   │   +── cam2_checkerboard_img1.jpg
│   │   │   +── cam2_checkerboard_img2.jpg
│   │   │   ...
│   │   │   +── intrinsics.json
│   │   +── cam3
│   │   │   +── cam3_checkerboard_img0.jpg
│   │   │   +── cam3_checkerboard_img1.jpg
│   │   │   +── cam3_checkerboard_img2.jpg
│   │   │   ...
│   │   │   +── intrinsics.json
│   │   +── multicapture
│   │   │   +── cam0
│   │   │   │   +── cam0_checkerborard_img_x.jpg
│   │   │   +── cam1
│   │   │   │   +── cam1_checkerborard_img_x.jpg
│   │   │   +── cam2
│   │   │   │   +── cam2_checkerborard_img_x.jpg
│   │   │   +── cam3
│   │   │   │   +── cam3_checkerborard_img_x.jpg
│   │   +── extrinsics.json
│   │   +── other_scene_images
```


### 3. COLMAP 형태의 cameras.txt, images.txt로 저장
- **입력:** intrinsics.json, extrinsics.json
- **목적:** COLMAP 형태의 카메라 파라미터 저장
- **출력:** cameras.txt, images.txt, points3D.txt(empty)

### 4. sparse/0/ 폴더 생성 후 3.에서 출력한 cameras.txt, images.txt, points3D.txt(empty)를 복사
https://colmap.github.io/faq.html#reconstruct-sparse-dense-model-from-known-camera-poses
If the camera poses are known and you want to reconstruct a sparse or dense model of the scene, you must first manually construct a sparse model by creating a cameras.txt, points3D.txt, and images.txt under a new folder:

python convert_to_COLMAP_fmt.py를 실행하면 다음과 같은 폴더가 생성되고, triangulation이 수행되어, triangulated/sparse/0 폴더가 생성됨
COLMAP의 model_convert를 통해 triangulated/sparse/0 폴더에 생성된 bin 파일을 txt 파일 형식으로도 변환하여 저장

```python
+── manually/created/sparse/model
│   +── cameras.txt
│   +── images.txt
│   +── points3D.txt
+── triangulated/sparse/0
│   +── cameras.txt
│   +── images.txt
│   +── points3D.txt
│   +── cameras.bin
│   +── images.bin
│   +── points3D.bin
```

The points3D.txt file should be empty while every other line in the images.txt should also be empty, since the sparse features are computed, as described below. You can refer to this article for more information about the structure of a sparse model.

#### COLMAP에서 Import Model로 sparse/0/ 폴더 선택하였으나 COLMAP Processing > Database management에서 Cameras와 Images가 모두 비어있음

COLMAP은 .txt 파일 기반의 모델을 GUI에서 직접 사용하지 않습니다. 대신 database.db를 직접 구성하거나 변환하여 사용하는 것이 유일한 방법입니다. GUI/CLI 모두 동일하게 database.db → 모든 이미지, 카메라, feature 정보 사용

The image reader can only take the parameters for a single camera. If you want to specify the parameters for multiple cameras, you would have to modify the SQLite database directly. This should be easy by modifying the scripts/python/database.py script.

### gaussian_splatting을 위해선 convert_to_COLMAP_fmt.py에서 OpenCV 카메라 모델을 사용하였기에, intrinsics를 사용하여, undistortion한 이미지를 사용하여야 함
- undistortion이 아직 안된 이미지들을 -> multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/scene/myface_undistort/input 에 넣기
- multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/scene/myface_undistort/distorted 폴더 안에 database.db와 triangulated/sparse/0 폴더를 복사

```python
<location>
|---input
|   |---<image 0>
|   |---<image 1>
|   |---...
|---distorted
    |---database.db
    |---sparse
        |---0
            |---...
```

# 아직 undistortion이 안된 images를 input 폴더에 넣고, convert.py를 실행하면 undistorted된 이미지들은 images 폴더에 생성됨
# triangulated/sparse/0에서 얻었던 cameras.txt, images.txt, points3D.txt -> distorted/sparse/0에 복사했음
# 미리 COLMAP의 feature extraction, feature matching을 실행하여, database.db에 저장했었기 때문에, convert.py에서는 feature extraction, feature matching을 실행하지 않음 -> convert.py에서 skip matching을 하면 feature extraction, feature matching, bundle adjustment을 실행하지 않음

### 나도.. convert_to_COLMAP_fmt.py에서 feature extraction, feature matching은 했지만, bundle adjustment는 실행하지 않았음 -> bundle adjustment도 추가하자

```
python convert.py -s multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/scene/myface_undistort --skip_matching
```

단 각 카메라마다 intrinsics가 달랐어서, undistortion된 이미지들의 사이즈가 다르게 생성됨

# 해결중인 부분..
cam0.jpg, cam1.jpg, cam2.jpg, cam3.jpg의 이미지 사이즈가 다르게 생성됨

### poses_bounds.npy 생성
git clone https://github.com/Fyusion/LLFF
python LLFF/imgs2poses.py multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/scene/myface_undistort



#### Question: How to format cameras.txt for Reconstruct sparse/dense model from known camera poses #428 
https://github.com/colmap/colmap/issues/428





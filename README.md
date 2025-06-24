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

#### Question: How to format cameras.txt for Reconstruct sparse/dense model from known camera poses #428 
different cameras with different intrinsics, multiple cameras의 parameters를 지정하려면 SQLite database를 직접 수정해야하고, 이는 `colmap/scripts/python/database.py` 스크립트로 가능하다
https://github.com/colmap/colmap/issues/428

#### gaussian_splatting을 위해선 convert_to_COLMAP_fmt.py에서 OpenCV 카메라 모델을 사용하였기에, intrinsics를 사용하여, undistortion한 이미지를 사용하여야 함
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
# 미리 COLMAP의 feature extraction, feature matching을 실행하여, database.db에 저장했었기 때문에, convert.py에서는 feature extraction, feature matching을 실행하지 않음 -> convert.py에서 skip matching을 하면 feature extraction, feature matching, mapper((SfM & triangulation) + bundle adjustment)을 실행하지 않음

### 본인은 convert_to_COLMAP_fmt.py에서 feature extraction, feature matching을 수행하고, 미리 PnP 알고리즘을 통해 계산한 카메라 포즈를 주었고, 이 카메라 포즈를 사용하여 point triangulator를 수행하였지만, bundle adjustment는 실행하지 않았음 -> bundle adjustment도 추가하자
### **Bundle Adjustment(BA)**를 수행하지 않으면 포즈 및 3D 구조 간의 정합 최적화가 이루어지지 않음
### 단, bundle adjustment는 feature matching에서 찾아진 대응점 관계가 부정확하면, triangulation으로 찾아진 3D 점들의 위치도 부정확해질 수 있고, bundle adjustment 결과도 부정확해질 수 있음
- BA는 기존의 3D 구조와 카메라 포즈를 정밀하게 정합하는 최적화 과정입니다.
- 하지만, **초기 입력값(3D 점, 대응점, 포즈)**이 부정확하거나 부족하다면, BA는:
- 오차를 줄이는 대신, 잘못된 방향으로 수렴하거나
- **과적합(overfitting)**의 형태로 수렴할 수 있음
- 3D 점의 밀도가 충분하지 않을 경우
- reconstruct된 3D 점들이 sparse하고, 장면 구조를 충분히 포괄하지 못하면:
- 카메라 포즈 간 제약 조건이 약해짐
- 대응점 기반 에러 최소화가 전체 장면 정합성으로 연결되지 않음
- 이런 경우 BA를 수행해도 최적화에 충분한 정보가 부족하여, 결과가 무의미하거나 오히려 나빠질 수 있음

### convert.py에서는 feature extraction, feature matching, mapper 가 수행되었고, mapper는 카메라 포즈 계산 (SfM)과 triangulation을 수행한 후에 (local+global) bundle adjustment를 수행함

```
python convert.py -s multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/scene/myface_undistort --skip_matching
```

각 카메라마다 intrinsics가 달랐어서, undistortion된 이미지들의 사이즈가 다르게 생성됨

## 카메라 내부파라미터 설정
- image_undistorter는 이미지를 ideal pinhole camera 모델로 변환하는 과정에서, projection 중심(cx, cy) 기준으로 유효한 시야 영역만을 유지함.
- 따라서 추정된 intrinsics의 cx, cy가 이미지 중심에서 크게 벗어난 경우, warped 영역이 이미지 밖으로 밀려 crop이 심하게 발생함
### camera_calibration_intrinsics.py에서 체커보드 패턴으로 추정한 intrinsics인 mtx에서 임의로 mtx[0,2] = W/2, mtx[1,2] = H/2로 대체하여서 crop이 심하게 되는 부분이 해결되었음
카메라의 **내부 파라미터(intrinsic parameters)**는 일반적으로 다음과 같은 세 가지 요소로 구성됩니다: 2D Translation Matrix, 2D Scaling Matrix, 그리고 2D Shear Matrix입니다.
- 2D Translation Matrix는 **principal point(주점)**의 위치를 나타내며, 이는 이미지 좌표계에서 광축이 통과하는 점입니다. **대부분의 경우, 이 주점은 이미지의 중심에 위치한다고 가정합니다.**
- 2D Shear Matrix는 이미지 축 간의 비직교성을 표현합니다. 그러나 실제 대부분의 카메라에서는 픽셀의 x, y축이 직교한다고 가정하기 때문에, 이 항은 무시되는 경우가 많습니다.
- 2D Scaling Matrix는 이미지의 x축과 y축 방향에 대한 **focal length(초점 거리)**를 나타냅니다. 초점 거리는 이미지 센서와 이미지 평면 사이의 거리로 해석할 수 있으며, 이 값은 카메라 캘리브레이션에서 핵심적으로 추정하는 파라미터입니다.
- 따라서 실제 응용이나 본 논문에서는 intrinsic parameters 중 focal length에 해당하는 scaling 요소만을 추정 대상으로 삼고 있으며, **나머지 요소들은 고정(principal point)**되거나 **무시(shear)**되는 경우가 많습니다.

## image_undistorter 명령
- 왜곡 제거된 이미지와 함께, 이 이미지에 맞는 ideal PINHOLE (또는 SIMPLE_PINHOLE) 카메라 모델을 생성함
- 'image undistorter' 명령을 수행한다고 해서 database.db 내 OpenCV 모델이 PINHOLE로 자동 변환되지는 않습니다.
- 대신, undistorted 결과에 대응하는 PINHOLE 모델이 별도 파일(cameras.txt 등)에 생성될 뿐입니다.

### poses_bounds.npy 생성
git clone https://github.com/Fyusion/LLFF
python LLFF/imgs2poses.py multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/scene/myface_undistort

### GS 학습 성공!
```python
<KIST_llff>
|---images
|   |---<image 0>
|   |---<image 1>
|   |---...
|---sparse
|    |---0
|        |---cameras.bin
|        |---images.bin
|        |---points3D.bin
|---poses_bounds.npy   
```

------------------------------------------------------------------------------------------------------------------
# To do list
- feature extraction을 dense하게 수행하는 알고리즘을 사용하고, feature matching을 수행하고, PnP 알고리즘으로 구한 카메라 포즈와 함께, 앞서 구한 feature matching으로 찾아진 correspondences가 2개 이상일 경우에도 triangulation하여 3D 포인트를 reconstruct하는 알고리즘을 구현해야하고, 추가적으로 카메라 포즈 및 3D 구조간의 정합 최적화를 위한 Bundle Adjustment(BA)를 수행해야만 함

### Triangulation with more than 3 correspondences (cv2.sfm)

- [OPENCV_EXTRA_MODULES에 sfm이 포함되어 있음](https://github.com/opencv/opencv_contrib/blob/master/modules/sfm/src/triangulation.cpp)
- `cv2.sfm` 모듈은 OpenCV의 contrib 모듈 중 하나이며, 기본 OpenCV 설치에는 포함되어 있지 않습니다. cv2.sfm을 사용하려면 OpenCV를 소스에서 직접 빌드해야함

### cv2.sfm을 사용하기 위한 python 3.12 가상환경 새로 구축
```python
conda create -n opencv_sfm_py312 python=3.12 -y
conda activate opencv_sfm_py312
pip install "numpy<2.0"
pip install matplotlib

cd submodules 
git clone https://github.com/Parskatt/DKM.git
cd ..
# DKM 설치시 opencv가 같이 깔림
pip install submodules/DKM 
# opencv 관련 라이브러리 제거
pip uninstall -y opencv-python opencv-python-headless

pip install torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu118
```

### Dense Matching Algorithm
- [DUSt3R](https://github.com/naver/dust3r)
- [MASt3R](https://github.com/naver/mast3r)
- [DKM](https://github.com/Parskatt/DKM)

DUSt3R 기본 모델로 pixel별 3D point를 예측했었습니다. 이 관계를 기반으로 아래 수식으로 focal length를 예측 할 수 있습니다.


## 🔍 용어 정리: "Dense Reconstruction"
Dense reconstruction은 일반적으로 MVS (Multi-View Stereo) 를 통해 장면의 표면을 조밀한 3D 포인트 클라우드 또는 mesh로 복원하는 것을 의미합니다.
이때는 triangulated sparse points가 아닌, 픽셀 단위로 대응점을 찾고 깊이 정보를 추정하여 수십만~수백만 개의 3D 점을 생성합니다.
→ COLMAP에서도 MVS를 사용한 patch_match_stereo, stereo_fusion 이후가 진짜 dense reconstruction입니다.

### 흔한 혼동: Dense feature 사용 = dense reconstruction?
어떤 연구나 구현에서는 dense feature matcher (e.g., LoFTR)만 사용해도 이를 "dense reconstruction"이라 부르는 경우가 있습니다. 하지만 엄밀히 보면 이건: dense correspondences 기반의 SfM 또는 dense SfM 이라고 부르는 게 더 정확합니다.
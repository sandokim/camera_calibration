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
  - extrinsics.json으로 카메라 포즈 저장 -> scene/myface/images/checkerboard -> scene/myface/images에 복사
+── scene/myface/images
│   +── cam0
│   +── cam1
│   +── cam2
│   +── cam3
│   +── extrinsics.json


### 3. COLMAP 형태의 cameras.txt, images.txt로 저장
- **입력:** intrinsics.json, extrinsics.json
- **목적:** COLMAP 형태의 카메라 파라미터 저장
- **출력:** cameras.txt, images.txt, points3D.txt(empty)

### 4. sparse/0/ 폴더 생성 후 3.에서 출력한 cameras.txt, images.txt, points3D.txt(empty)를 복사
https://colmap.github.io/faq.html#reconstruct-sparse-dense-model-from-known-camera-poses
camera poses
If the camera poses are known and you want to reconstruct a sparse or dense model of the scene, you must first manually construct a sparse model by creating a cameras.txt, points3D.txt, and images.txt under a new folder:

```python
+── path/to/manually/created/sparse/model
│   +── cameras.txt
│   +── images.txt
│   +── points3D.txt
```

The points3D.txt file should be empty while every other line in the images.txt should also be empty, since the sparse features are computed, as described below. You can refer to this article for more information about the structure of a sparse model.

#### COLMAP에서 Import Model로 sparse/0/ 폴더 선택하였으나 COLMAP Processing > Database management에서 Cameras와 Images가 모두 비어있음

COLMAP은 .txt 파일 기반의 모델을 GUI에서 직접 사용하지 않습니다.

대신 database.db를 직접 구성하거나 변환하여 사용하는 것이 유일한 방법입니다.

GUI/CLI 모두 동일하게 database.db → 모든 이미지, 카메라, feature 정보 사용

The image reader can only take the parameters for a single camera. If you want to specify the parameters for multiple cameras, you would have to modify the SQLite database directly. This should be easy by modifying the scripts/python/database.py script.

### poses_bounds.npy 생성
https://github.com/Fyusion/LLFF

python LLFF/imgs2poses.py LLFF/scene/KIST_llff

### gaussian_splatting을 위해선 convert_to_COLMAP_fmt.py에서 OpenCV 카메라 모델을 사용하였기에, intrinsics를 사용하여, undistortion한 이미지를 사용하여야 함
undistortion이 아직 안된 이미지들을을 -> \LLFF\scene\KIST_llff\input 에 넣고
\LLFF\scene\KIST_llff\distorted 폴더 안에 database.db와 triangulated 폴더 안에 sparse/0 폴더를 복사
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

다음을 실행하면 undistorted된 이미지들이 images 폴더에 생성됨
```
python convert.py -s LLFF\scene\KIST_llff --skip_matching
```
단 각 카메라마다 intrinsics가 달랐어서, undistortion된 이미지들의 사이즈가 다르게 생성됨

cam0.jpg, cam1.jpg, cam2.jpg, cam3.jpg의 이미지 사이즈가 다르게 생성됨, cam3.jpg는 intrinsics가 부정확한지 너무 crop이 국소적으로 되어 이미지가 만들어짐 (960x540->192x108)


If you have your own COLMAP dataset without undistortion (e.g., using OPENCV camera), you can try to just run the last part of the script: Put the images in input and the COLMAP info in a subdirectory distorted:

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

Then run

python convert.py -s <location> --skip_matching [--resize] #If not resizing, ImageMagick is not needed


#### Question: How to format cameras.txt for Reconstruct sparse/dense model from known camera poses #428 
https://github.com/colmap/colmap/issues/428


# **Reconstruct sparse/dense model from known camera poses**
keypoints와 matches가 제대로 불러와지지 않아서 triangulation이 안되는 문제 해결중






### 5. COLMAP points3D.txt를 위한 cameras.txt, images.txt 활용 및 sparse 3D 모델 생성
- **입력:** cameras.txt, images.txt, 체커보드를 촬영한 멀티 카메라 세팅에서 촬영된 이미지
- **목적:** COLMAP을 통한 3D 모델 생성
- **출력:** points3D.txt




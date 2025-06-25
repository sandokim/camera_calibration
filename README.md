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


### 4. [sparse/0/ 폴더 생성 후 3.에서 출력한 cameras.txt, images.txt, points3D.txt(empty)를 복사](https://colmap.github.io/faq.html#reconstruct-sparse-dense-model-from-known-camera-poses)
If the camera poses are known and you want to reconstruct a sparse or dense model of the scene, you must first manually construct a sparse model by creating a `cameras.txt, points3D.txt`, and `images.txt` under a new folder:

`python convert_to_COLMAP_fmt.py`를 실행하면 다음과 같은 폴더가 생성되고, triangulation이 수행되어, `triangulated/sparse/0` 폴더가 생성됨
COLMAP의 `model_convert`를 통해 `triangulated/sparse/0` 폴더에 생성된 `bin` 파일을 `txt` 파일 형식으로도 변환하여 저장

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

The image reader can only take the parameters for a single camera. If you want to specify the parameters for multiple cameras, you would have to modify the SQLite database directly. This should be easy by modifying the `scripts/python/database.py` script.

#### Question: How to format cameras.txt for Reconstruct sparse/dense model from known camera poses #428 
[different cameras with different intrinsics, multiple cameras의 parameters를 지정하려면 SQLite database를 직접 수정해야하고, 이는 `colmap/scripts/python/database.py` 스크립트로 가능하다.](https://github.com/colmap/colmap/issues/428)

#### gaussian_splatting을 위해선 convert_to_COLMAP_fmt.py에서 OpenCV 카메라 모델을 사용하였기에, intrinsics를 사용하여, undistortion한 이미지를 사용하여야 함
- undistortion이 아직 안된 이미지들을 -> `multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/scene/myface_undistort/input` 에 넣기
- `multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/scene/myface_undistort/distorted` 폴더 안에 `database.db`와 `triangulated/sparse/0` 폴더를 복사
- `triangulated/sparse/0`에서 얻었던 `cameras.txt, images.txt, points3D.txt` -> `distorted/sparse/0`에 복사했음

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

- `convert.py`를 실행하면 undistorted된 이미지들은 `images` 폴더에 생성됨

```python
<location>
├── input/                   # (1) 원본 이미지 (왜곡 포함)
│   ├── image0.jpg
│   ├── image1.jpg
│   └── ...
├── distorted/              # (2) COLMAP 작업 공간 (왜곡 포함)
│   ├── database.db         # COLMAP용 DB (왜곡 포함 이미지 기준)
│   └── sparse/
│       └── 0/
│           └── cameras.bin
│           └── images.bin
│           └── points3D.bin
├── images/                 # (3) Undistorted 이미지 (Pinhole 기준 변환됨)
├── sparse/                 # (4) Undistorted 기준 재구성 결과
│   └── 0/
│       └── cameras.bin
│       └── images.bin
│       └── points3D.bin
```

- 미리 COLMAP의 feature extraction, feature matching을 실행하여, `database.db`에 저장했었기 때문에, `convert.py`에서는 feature extraction, feature matching을 실행하지 않음 -> `convert.py`에서 skip matching을 하면 feature extraction, feature matching, mapper((SfM & triangulation) + bundle adjustment)을 실행하지 않음
- 본인은 `convert_to_COLMAP_fmt.py`에서 feature extraction, feature matching을 수행하고, 미리 PnP 알고리즘을 통해 계산한 카메라 포즈를 주었고, 이 카메라 포즈를 사용하여 point triangulator를 수행하였지만, bundle adjustment는 실행하지 않았음 -> bundle adjustment도 추가하자
  <p align="center">
    <img src="https://github.com/user-attachments/assets/90ac44df-36aa-4389-8d69-41d78d6ba8b5" width="600"/>
  </p>
  <p align="center"><em>Structure-from-Motion (SfM) Pipeline : [Source](http://theia-sfm.org/sfm.html)</em></p>
- Traditional SfM pipelines such as COLMAP, operate by taking a sequence of images, detecting features points and descriptors images and matching these features across different views. RANSAC is then used to filter out bad matches while maximizing inliers. Using triangulation, camera poses are estimated and iteratively refined using Bundle Adjustment (BA) with an objective to minimize reprojection errors.

###  Limitations of Traditional SfM:
- Traditional SfM methods require the camera intrinsics to be known beforehand limiting their applicability in scenarios where camera parameters are unknown or missing. **These methods typically consider only a handful of keypoints to obtain sparse point clouds discarding the global geometric context of the scene.** They are often time consuming and complex, involving multiple intermediate stages potentially introducing noise. They don’t handle scenes with low texture or repetitive patters well. **Bundle adjustment, a key step in refining 3D points is computationally intensive especially for larger scenes.** They require highly overlapping image sequences and camera motion for accurate reconstruction.
- SfM은 오직 몇개의 keypoints만 고려해서 sparse point clouds를 얻기 때문에 scene에 대한 global geometric context 정보를 무시한다.
- SfM에서 bundle adjustment는 3D points를 refine하는데 핵심적인 연산이지만, computationally intensive하다.
- DUSt3R이 single forward pass로 traditional SfM의 복잡한 파이프라인 없이 좋은 estimate를 주었지만, DUSt3R은 부정확한 global SfM reconstruction이다.
- MASt3R이 DUSt3R에서 발전시켜 matching image pairs에 강인하게 디자인 되었지만 larger scenes에 대해서는 scale하지 못한다.
- MASt3R-SfM은 COLMAP-SfM의 Bundle Adjustment를 제거해서 연산 속도를 빠르게 하였고, Gaussian Splatting에 initial을 만들때 바로 쓸 수 있다.

- BA는 기존의 3D 구조와 카메라 포즈를 정밀하게 정합하는 최적화 과정입니다. **bundle adjustment에서는 2D reprojection error를 최소화합니다.** Bundle Adjustment(BA)를 수행하지 않으면 포즈 및 3D 구조 간의 정합 최적화가 이루어지지 않음. 단, bundle adjustment는 feature matching에서 찾아진 대응점 관계가 부정확하면, triangulation으로 찾아진 3D 점들의 위치도 부정확해질 수 있고, bundle adjustment 결과도 부정확해질 수 있음. 즉, 초기 입력값(3D 점, 대응점, 포즈)이 부정확하거나 부족하다면, BA는 오차를 줄이는 대신, 잘못된 방향으로 수렴하거나 과적합(overfitting)의 형태로 수렴할 수 있음
- 3D 점의 밀도가 충분하지 않을 경우, reconstruct된 3D 점들이 sparse하고, 장면 구조를 충분히 포괄하지 못하면 카메라 포즈 간 제약 조건이 약해짐. 대응점 기반 에러 최소화가 전체 장면 정합성으로 연결되지 않음. 이런 경우 BA를 수행해도 최적화에 충분한 정보가 부족하여, 결과가 무의미하거나 오히려 나빠질 수 있음

### convert.py에서는 feature extraction, feature matching, mapper 가 수행되었고, mapper는 카메라 포즈 계산 (SfM)과 triangulation을 수행한 후에 (local+global) bundle adjustment를 수행함

```
python convert.py -s multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/scene/myface_undistort --skip_matching
```

각 카메라마다 intrinsics가 달랐어서, undistortion된 이미지들의 사이즈가 다르게 생성됨

## 카메라 내부파라미터 설정
- image_undistorter는 이미지를 ideal pinhole camera 모델로 변환하는 과정에서, projection 중심(cx, cy) 기준으로 유효한 시야 영역만을 유지함.
- 따라서 추정된 intrinsics의 cx, cy가 이미지 중심에서 크게 벗어난 경우, warped 영역이 이미지 밖으로 밀려 crop이 심하게 발생함
- **camera_calibration_intrinsics.py에서 체커보드 패턴으로 추정한 intrinsics인 mtx에서 임의로 mtx[0,2] = W/2, mtx[1,2] = H/2로 대체하여서 crop이 심하게 되는 부분이 해결되었음**
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
```python
git clone https://github.com/Fyusion/LLFF
python LLFF/imgs2poses.py multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/scene/myface_undistort
```

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

## Triangulation with more than 3 correspondences (cv2.sfm)
### [MATLAB triangulateMultiview](https://www.mathworks.com/help/vision/ref/triangulatemultiview.html)
triangulateMultiview 3-D locations of world points matched across multiple images

worldPoints = triangulateMultiview(pointTracks,cameraPoses,intrinsics) returns the locations of 3-D world points that correspond to points matched across multiple images taken with calibrated cameras. **pointsTracks specifies an array of matched points**. cameraPoses and intrinsics specify camera pose information and intrinsics, respectively. The function does not account for lens distortion.
[worldPoints,reprojectionErrors] = triangulateMultiview(__) additionally returns the mean reprojection error for each 3-D world point using all input arguments in the priro syntax.
[worldPoints,reprojectionErrors,validIndex] = triangulateMultiview(__) additionally returns the indices of valid and invalid world points. Valid points are locaed in front of the cameras.

Load images in the workspace
**Load precomputed cameraparameters** --> Get camera intrinsics parameters
Compute features for the first images.
```python
I = im2gray(readimage(imds,1));;
**I = undistortImage(I,intrinsics);**
pointsPrev = detectSURFFeatures(I);;
[featuresPrev,pointsPrev] = extractFeatures(I,pointsPrev);;
```

Load camera poses.
Creae an imageviewset object
vSet = imageviewset;
vSet = addView(vSet,1,absPoses(1),Points=pointsPrev);

Compute features and matches for the rest of the images.
for i = 2:numel(imds.Files)
  I = im2gray(readimage(imds,i));
  I = undistortImage(I,intrinsics);
  points = detectSURFFeatures(I);
  [features,points] = extractFeatures(I,points);
  vSet = addView(vSet,i,absPoses(i),Points=points);
  pairsIdx = matchFeatures(featuresPrev,features,MatchThreshold=5);
  vSet = addConnection(vSet,i-1,i,Matches=pairsIdx);
  featuresPrev = features;
end

Find point tacks.
tracks = findTracks(vSet);
get camera poses.
caneraPoses = poses(vSet);
Find 3-D world points.
[xyzPoints,errors] = triangulateMultiview(tracks,cameraPoses,intrinsics);
z = xyzPoints(:,3);
idx = errors < 5 & z > 0 & z < 20;
pcshow(xyzPoints(idx, :),AxesVisibility="on",VerticalAxis="y",VerticalAxisDir="down",MarkerSize=30);
hold on
plotCamera(cameraPoses, Size=0.2);
hold off

### [MATLAB matchFeatures](https://www.mathworks.com/help/vision/ref/matchfeatures.html?searchHighlight=matchFeatures&s_tid=srchtitle_support_results_1_matchFeatures)
matchFeatures Find matching features

indexPairs = matchFeatures(features1,features2) returns indices of the matching features in the two input feature sets. The input feature must be either binaryFeatures objects or matrices.
[indexPairs,matchmetric] = matchFeatures(features1,features2) also returns the distance between the matching features, indexed by indexPairs.
[indexPairs,matchmetric] = matchFeatures(features1,features2,Name=Value) specifies options using one or more name-value arguments in addition to any combination of arguments from previous syntaxes. For example, matchFeatures(__,Method="Exhaustive") sets the matching method to Exhaustive.

Find Corresponding Interest Points Between Pair of Images
Find corresponding interest points between a pair of images using local neighborhoods and the Harris algorithm.
Read the stereo images.
I1 = im2gray(imread("viprectification_deskLeft.png"));
I2 = im2gray(imread("viprectification_deskRight.png"));

Find the corners.
points1 = detectHarrisFeatures(I1);
points2 = detectHarrisFeatures(I2);

Extract the neighborhood features.
[features1,valid_points1] = extractFeatures(I1,points1);
[features2,valid_points2] = extractFeatures(I2,points2);

Match the features.
indexPairs = matchFeatures(features1,features2);

Retrieve the locations of the corresponding points for each image.
matchedPoints1 = valid_points1(indexPairs(:,1),:);
matchedPoints2 = valid_points2(indexPairs(:,2),:);

Visualize the corresponding points. You can see the effect of translation between the two images despite several eeroneous matches.
figure;
showMatchedFeatures(I1,I2,matchedPoints1,matchedPoints2);

Find Corresponding Points Using SURF Features
Read the two images.
I1 = imread("cameraman.tif");
I2 = imresize(imrotate(I1,-20),1.2);

Find the SURF features.
points1 = detectSURFFeatures(I1);
points2 = detectSURFFeatures(I2);

Extract the features.
[f1,vpts1] = extractFeatures(I1,points1);
[f2,vpts2] = extractFeatures(I2,points2);

Retrieve the locations of matched points.
indexPairs = matchFeatures(f1,f2);
matchedPoints1 = vpts1(indexPairs(:,1));
matchedPoints2 = vpts2(indexPairs(:,2));

Display the matching points. The data still includes several outliers, but you can see the effects of rotation and scaling on the display of matched features.

figure; showMatchedFeatures(I1,I2,matchedPoints1,matchedPoints2);
legend("matched points 1","matched points 2");

### [MATLAB findTracks](https://www.mathworks.com/help/vision/ref/imageviewset.findtracks.html)

findTracks -> Find matched points across multiple views

tracks = findTracks(vSet) finds and returns point tracks across multiple views in the view set, vSet. Each track contains 2-D projections of the same 3-D world point.
tracks = findTracks(vSet, viewIds) finds point tracks across a subset of views specified by viewIds.
tracks = findTracks(__, 'MinTrackLength', trackLength) specifies the minimum length of the tracks.

Compute features for the first image.
I = im2gray(readimage(images,1));
pointsPrev = detectSURFFeatures(I);
[featuresPrev,pointsPrev] = extractFeatures(I,pointsPrev)

Create an image view set and add one view to the set.
vSet = imageviewset;
Vset = addView(vSet,1,'Features',featuresPrev,'Points',pointsPrev);

Compute features and matches for the rest of the images.
for i = 2:numel(images.Files)
  I = im2gray(readimage(images,i));
  points = detectSURFFeatures(I);
  [features, points] = extractFeatures(I,points);
  vSet = addView(vSet,i,'Features',features,'Points',points);
  pairsIdx = matchFeatures(featuresPrev,features);
  vSet = addConnection(vSet,i-1,i,'Matches',pairsIdx);
  featuresPrev = features;
end

Find point tracks across views in the image view set.
tracks = findTracks(vSet);

vSet -- Image view set 
Image view set, specified as an imageviewset object.

### [MATLAB imageviewset](https://www.mathworks.com/help/vision/ref/imageviewset.html)
Manage data for structure-from-motion, visual odometry, and visual SLAM

The imageviewset object manages view attributes and pairwise connections between views of data used in structure-from-motion, visual odometry, and simultaneous localization and mapping (SLAM) data. View attributes can be feature descriptors, feature points, or absolute camera poses. Pairwise connections between views can be point matches, relative camera poses, or an information matrix. You can also use this object to find point tracks used by triangulateMultiview and bundleAdjustment functions.

vSet = imageviewset() returns an imageviewset object. You can add views and connections using the addView and addConnection object functions.

### [MATLAB addView](https://www.mathworks.com/help/vision/ref/imageviewset.addview.html)
addView add view to view set

vSet = addView(vSet,viewID) adds the view specified by viewID to the view set, vSet.
vSet = addView(vSet,viewID,absPose) specifies the absolute pose of the view.
vSet = addView(__,Name,Value) specifies options using one or more name-value arguments in addition to any of the input argument combination in previous syntaxes.
vSet = addView(vSet,viewTable) adds one or more views in the table specified by viewTable.

Create an empty image view set.
vSet = imageviewset;

Detect interest points in the image.
points = detectSURFFeatures(im2gray(I))

Add the interest points as a view to the image view set.
vSet = addView(vSet,1,'Points',points);

### [MATLAB addConnection](https://www.mathworks.com/help/vision/ref/imageviewset.addconnection.html)
addConnection Add connection between views in view set

vSet = addConnection(vSet,viewId1,viewId2) adds a connection between views viewId1 and viewId2 to the view set, vSet.
vSet = addConnection(vSet,viewId1,viewId2,relPose) specifies the relative pose of viewId2 with respect to viewId1.
vSet = addConnection(vSet,viewId1,viewId2,relPose,infoMat) specifies the information matrix associated with the connection.
vSet = addConnection(__,"Matches",featureMatches) specifies the indices of matched points between two views in addition to any of the input argument combinations in previous syntaxes.

Create an empty image view set.
vSet = imageviewset;

Read two images into the workspace
I1 = im2gray(imread(fullfile(imageDir,'image1.jpg')));
I2 = im2gray(imread(fullfile(imageDir,'image2.jpg')));

Detect interest points in each image.
points1 = detectSURFFeatures(I1);
points2 = detectSURFFeatures(I2);

Extract feature descriptors from the interest points.
[features1,validPoints1] = extractFeatures(I1,points1);
[features2,validPoints2] = extractFeatures(I2,points2);

Add teh features and points for the two images to the image view set.
vSet = addView(vSet,1,'Features',features1,'Points',validPoints1);
vSet = addView(vSet,2,'Features',features2,'Points',validPoints2);

Match teh features between the two images.
indexPairs = matchFeatures(features1,features2);

Store the matched features as a connection in the image view set.
vSet = addConnection(vSet,1,2,'Matches',indexPairs);

### [MATLAB extractFeatures](https://www.mathworks.com/help/vision/ref/extractfeatures.html)
extractFeatures Extract interest point descriptors

[features,validPoints] = extractFeatures(I,points) returns **extracted feature vectors, also known as descriptor**, and their corresponding locations, from a binary or intensity image. The function derives the descriptors from pixels surrounding an interest point. The pixels represent and match features specified by a single-point location. Each single-point specifies the center location of a neighborhood. The method you use for descriptor extraction depends on the class of the input points.
[features,validPoints] = extractFeatures(I,points,Name=Value) specifies options using one or more name-value arguments in addition to any combination of arguments from previous syntaxes. For example, extractFeatures(I,points,Method="Block") sets teh method to extract descriptor to Block.

Extract Corner Features from an Image
Read the image
I = imread("cameraman.tif")
 
Find and extract corner features from the image.
corners = detectHarrisFeatures(I);
[features,valid_corners] = extractFeatures(I,corners);

Extract SURF Features from an Image
Read image
I = imread("camearman.tif")

Find and extract features from the input image.
points = detectSURFFeatures(I);
[features,valid_points] = extractFeatures(I,points);


### [MATLAB bundleAdjustment](https://www.mathworks.com/help/vision/ref/bundleadjustment.html)
bundleAdjustment **Adjust collection of 3-D points and camera poses**

[xyzRefinedPoints,refinedPoses] = bundleAdjustment(xyzPoints,pointTracks,cameraPoses,intrinsics) refines 3-D points and camera poses to minimize reprojection errors. The refinement procedure is a variant of the Levenberg-Marquardt algorithm. The function **uses the same global reference coordinate system to return both the 3-D points and camera poses.**
[wpSetRefined,vSetRefined,pointIndex] = bundleAdjustment(wpSet,vSet,viewIds,intrinsics) refines 3-D points from the world point set, wpSet, and refines camera poses from the image view set, vSet. viewIds specify the camera poses in vSet to refine.
[__,reprojectionErrors] = bundleAdjustment(__) returns the mean reprojection error for each 3-D world point, in addition to the arguments from the previous syntax.
[__] = bundleAdjustment(__,Name=Value) specifies options using one or more name-value arguments in addition to any combination of arguments from previous syntaxes. For example, **MaxIterations=50 sets the number of iterations to 50**. Unspecified arguments have default values.

Load data for initialization.
data = load("globalBA.mat")
Refine the camera poses and points.
[xyzRefinedPoints,refinedPoses] = ...
  bundleAdjustment(data.xyzPoints,data.pointTracks,data.cameraPoses,data.intrinsics);
Display the 3-D points and camera poses before and after refinement.
pcshowpair(pointCloud(data.xyzPoints), pointCloud(xyzRefinedPoints), ...
    AxesVisibility="on", VerticalAxis="y", VerticalAxisDir="down", MarkerSize=40);
hold on
plotCamera(data.cameraPoses, Size=0.1, Color="m");
plotCamera(refinedPoses, Size=0.1, Color="g");
legend("Before refinement", "After refinement", color="w");

Input Arguments
xyzPoints: Unrefined 3-D points, specified as an M-by-3 matrix of [x y z] locations.
pointTracks: Matching points across multiple images, specified as an N-element array of pointTrack objects. Each element contains two or more matching points across multiple images.
cameraPoses: Camera pose information, specified as a two-column table with columns ViewId and AbsolutePose. The view IDs relate to the IDs of the objects in the pointTracks argument. You can use the poses object function to obtain cameraPoses table.
intrinsics: Camera intrinsics, specified as a cameraIntrinsics object or an N-element array of cameraIntrinsics objects. N is the number of camera poses or the number of IDs in viewIDs. Use a single cameraIntrinsics object when images are captured using the same camera. Use a vector cameraIntrinsics objects when images are captured by different cameras.
wpSet: 3-D world points, specified as a worldpointset object.
vSet: Camera poses, specified as an imageviewset object.
viewIDs: View identifiers, specified as an N-element array. The viewIDs represent which camera poses to refine specifying their related views in imageviewset.

Name-Value Arguments
MaxIterations: Maximum number of iterations before the Levenberg-Marquardt algorithm stops, specified as a positive integer.
AbsoluteTolerance: Absolute termination tolerance of the mean squared reprojection error in pixels, specified as positive scalar.
RelativeTolerance: Relative termination tolerance of the reduction in reprojection error between iterations, specified as positive scalar.
PointsUndistorted: Flag to indicate lens distortion, specified as false or true. **When you set PointsUndistorted to false, the 2-D points in pointTracks or in vSet must be from images with lens distortion.** **To use undistorted points, first use the undistortImage function to remove distortions from the images, then set PointsUndistorted.**
FixedViewIDs: View IDs for fixed camera pose, specified as a vector of nonnegative integers. Each ID corresponds to the ViewId of a fixed camera pose in cameraPoses. An empty value for FixedViewIDs means that all camera poses are optimized.

Output Arguments
reprojectionErrors: Reprojection errors, returned as an M-element vector. The function projects each world point back into each camera. Then, in each image, the function calculates the reprojection error as the distance between the detected and the reprojected point. The reprojectionErrors vector contains the average reprojection error for each world point.

  <p align="center">
    <img src="https://github.com/user-attachments/assets/4b6664c1-f424-465f-b27f-0bc74c9ca0ed" width="600"/>
  </p>
  <p align="center"><em>Reprojection Errors</em></p>




### [OpenCV triangulatePoints 함수](https://docs.opencv.org/4.x/d0/dbd/group__triangulation.html)
- Triangulates the 3d position of 2d correspondences between several images. Reference: Internally it uses DLT method [119] 12.2 pag.312
- [119] Richard Hartley and Andrew Zisserman. Multiple view geometry in computer vision. Cambridge university press, 2003.
- cv2.sfm.triangulatePoints(InputArrrayOfArrays points2d, InputArrayOfArrays projection_matrices, OutputArray points3d)
  - 제공된 코드의 핵심은 2개 뷰(2-view)의 경우와 3개 이상의 뷰(N-view)의 경우를 나누어 처리하며, 두 경우 모두 DLT(Direct Linear Transformation) 원리를 기반으로 3D 좌표를 계산한다는 점입니다.
  - 뷰의 개수(nviews)가 정확히 2개일 경우, triangulateDLT 함수를 각 점 쌍에 대해 호출합니다.
    - 2-뷰의 경우(triangulateDLT): 각 대응점 쌍으로부터 4개의 선형 방정식을 만들어 AX=0 시스템을 구성하고, SVD를 이용해 X를 직접 풉니다. 이는 책 12.2절에 기술된 표준 DLT 방법과 정확히 일치합니다. 
  - 뷰의 개수가 2개보다 많을 경우, triangulateNViews 함수를 각 점 트랙에 대해 호출합니다.
    - 다중 뷰의 경우(triangulateNViews): 3D 점 X와 각 뷰의 깊이 스케일 λi를 모두 미지수로 두는 더 큰 선형 시스템을 구성합니다. SVD를 통해 이 시스템을 푼 뒤, 3D 점에 해당하는 부분만 추출하여 최종 결과를 얻습니다. 이 방법은 모든 뷰의 정보를 동시에 활용하여 더 안정적이고 정확한 결과를 얻을 수 있습니다.

  - 다중 뷰(3개 이상)에 대해 이 함수를 호출하기 위해 필요한 입력은 `points2d`와 `projection_matrices` 두 가지입니다.
    - points2d: 2D 대응점 데이터
      - 이 매개변수는 여러 뷰에 걸쳐 추적된 2D 점들의 집합입니다.
      - 예를 들어, 3개의 뷰에서 100개의 점을 삼각측량한다면:
        - points2d는 3개의 Mat 객체를 담고 있는 vector가 됩니다.
        - 각 Mat은 2x100 크기를 가집니다.
        - points2d[0].col(5)는 첫 번째 뷰의 6번째 점의 (x,y) 좌표입니다.
        - points2d[1].col(5)는 두 번째 뷰의 6번째 점의 (x,y) 좌표입니다.
        - points2d[2].col(5)는 세 번째 뷰의 6번째 점의 (x,y) 좌표입니다.
        - 이 세 점 points2d[0].col(5), points2d[1].col(5), points2d[2].col(5)는 모두 동일한 3D 공간상의 한 점에서 투영된 것이어야 합니다.
    - `projection_matrices`: 투영 행렬 데이터
      - 이 매개변수는 각 뷰에 해당하는 카메라의 투영 행렬(카메라 행렬) 집합입니다.
      - 벡터의 크기는 전체 뷰의 개수 m으로, points2d 벡터의 크기와 정확히 일치해야 합니다.
      - 벡터의 각 요소인 cv::Mat 객체는 3x4 크기를 가집니다.
      - 모든 투영 행렬 P_i는 반드시 동일한 월드 좌표계(world coordinate system)를 기준으로 표현되어야 합니다.
      - 이 행렬들은 일반적으로 사전 단계에서 계산됩니다. 예를 들어, Fundamental Matrix 또는 Trifocal Tensor를 계산한 뒤 이로부터 카메라 행렬을 복원하거나(projective reconstruction), 번들 조정(bundle adjustment)을 통해 얻어진 결과물일 수 있습니다.
      - 각기 다른 시점에 독립적으로 캘리브레이션된 카메라 행렬들을 그대로 사용하면, 각 카메라가 자신만의 월드 좌표계를 가지므로 올바른 삼각측량이 불가능합니다.

- 사용자께서 MASt3R로 구현한 pairwise matching은 Correspondence Tracking의 훌륭한 첫 단계입니다. 이를 다중 뷰 트래킹으로 확장하는 전체적인 파이프라인은 다음과 같습니다.
  - Pairwise Matching: 인접한 이미지 쌍들에 대해 MASt3R를 실행하여 matches(i, i+1)를 구합니다.
  - Track Chaining: 이 쌍별 매칭들을 연결하여 긴 후보 트랙들을 생성합니다.
  - Robust Verification: RANSAC과 Trifocal Tensor를 이용하여 후보 트랙들 중 기하학적으로 올바른 inlier 트랙들만 선별합니다. 이 과정은 책의 Algorithm 16.4에 잘 설명되어 있습니다.
  - 이렇게 최종적으로 얻어진 inlier 대응점 트랙들이 바로 cv::sfm::triangulatePoints 함수의 points2d 입력으로 사용될 고품질 데이터입니다. 이 데이터와 함께, RANSAC 과정에서 얻은 카메라 행렬들(Trifocal Tensor로부터 복원)을 projection_matrices 입력으로 주면, 매우 정확하고 안정적인 다중 뷰 삼각측량을 수행할 수 있습니다.

### Correspondence Tracking을 위한 단계별 절차
#### 1단계: 순차적 쌍별 매칭 (Sequential Pairwise Matching)
- 사용자께서 이미 구현하신 코드가 이 단계에 해당합니다. m개의 뷰(이미지)가 있다면, 인접한 모든 이미지 쌍에 대해 MASt3R 코드를 실행합니다.
  - view 1과 view 2 사이의 매칭 matches(1,2)를 구합니다.
  - view 2와 view 3 사이의 매칭 matches(2,3)를 구합니다.
  - view 3과 view 4 사이의 매칭 matches(3,4)를 구합니다.
  - ...
  - view m-1과 view m 사이의 매칭 matches(m-1,m)을 구합니다.
  - 이 단계의 결과물은 여러 개의 독립적인 2-view 대응점 목록입니다.

#### 2단계: 매칭 연결을 통한 후보 트랙 생성 (Chaining Matches to Form Putative Tracks)
- 이제 각 쌍별 매칭 결과를 연결하여 여러 프레임에 걸친 트랙을 만듭니다. 가장 간단한 방법은 다음과 같습니다.
  - matches(1,2)에서 한 대응점 쌍 (p1, p2)를 선택합니다. p1은 view 1의 점, p2는 view 2의 점입니다. 이것이 트랙의 시작입니다.
  - matches(2,3) 목록에서 p2와 일치하거나 매우 가까운 점을 찾습니다. 만약 (p2, p3)라는 매칭을 찾았다면, 트랙을 (p1, p2, p3)로 확장합니다.
  - 다시 matches(3,4) 목록에서 p3에 해당하는 점 p4를 찾아 트랙을 (p1, p2, p3, p4)로 확장합니다.
  - 이 과정을 더 이상 연결할 매칭이 없을 때까지 반복합니다.
  - 이 과정을 모든 matches(1,2)의 대응점에 대해 수행하면, 여러 개의 다양한 길이를 가진 후보 트랙(putative tracks) 집합이 생성됩니다. 하지만 이 방법은 각 단계에서 작은 오차가 누적되어 '표류(drift)'가 발생할 수 있으며, 잘못된 매칭이 포함될 수 있습니다. 따라서 기하학적 검증이 반드시 필요합니다.

#### 3단계: 다중 뷰 기하학을 이용한 강인한 검증 (Robust Geometric Verification)
- 이 단계가 바로 제공해주신 Hartley & Zisserman 책의 이론이 결정적인 역할을 하는 부분입니다. 단순히 연결만 된 트랙은 기하학적으로 올바르다는 보장이 없습니다. 책의 Chapter 15와 16에서 설명하는 **삼중초점 텐서(Trifocal Tensor)**를 사용하면 3개 뷰에 걸친 대응점의 유효성을 매우 강력하게 검증할 수 있습니다.
- Trifocal Tensor를 이용한 검증:
  - Trifocal Tensor의 핵심 기능 중 하나는 전송(Transfer) 입니다 (책의 Section 15.3 참조).
  - 두 뷰(예: view 1과 view 2)에서 대응점 (p1, p2)가 주어지면, Trifocal Tensor는 세 번째 뷰에서 해당 점 p3가 나타나야 할 정확한 위치 p3_predicted를 계산해낼 수 있습니다.
  - 이는 2개 뷰에서 단지 'epipolar line 위에 있어야 한다'는 제약보다 훨씬 강력합니다. 이 원리를 이용해 다음과 같이 잘못된 트랙을 걸러낼 수 있습니다.
- RANSAC 프레임워크 적용 (Algorithm 16.4 참조):
  - 2단계에서 생성된 수많은 후보 트랙 중에서 무작위로 6개의 트랙을 샘플링합니다. (Trifocal Tensor는 최소 6개의 점 대응으로 계산할 수 있습니다 ).
  - 이 6개의 트랙을 이용해 Trifocal Tensor T를 계산합니다.
  - 계산된 T를 사용하여 나머지 모든 트랙들의 유효성을 검사합니다. 각 트랙 (p1, p2, p3)에 대해, p1과 p2를 이용해 세 번째 뷰의 점 위치 p3_predicted를 전송(transfer)합니다.
  실제 측정된 p3와 예측된 p3_predicted 사이의 거리(재투영 오차)를 계산합니다. d(p3, p3_predicted).
  - 이 거리가 미리 정해둔 임계값 t보다 작으면, 해당 트랙을 **정상값(inlier)**으로 간주합니다.
  - 가장 많은 수의 inlier를 확보하는 Trifocal Tensor T를 최종 모델로 선택합니다.
- 최종 대응점 트랙 확보:
  - RANSAC 과정에서 가장 많은 지지를 받은 Trifocal Tensor 모델과 일관성을 보인 inlier 트랙들이 바로 우리가 찾던, 기하학적으로 검증된 최종 대응점 트랙이 됩니다.



### cv2.sfm을 사용하기 위한 python 3.11 가상환경 새로 구축 (mast3r의 faiss-gpu 사용을 위해 CUDA 12.1로 설치)
- [OPENCV_EXTRA_MODULES에 sfm이 포함되어 있음](https://github.com/opencv/opencv_contrib/blob/master/modules/sfm/src/triangulation.cpp)
- `cv2.sfm` 모듈은 OpenCV의 contrib 모듈 중 하나이며, 기본 OpenCV 설치에는 포함되어 있지 않습니다. cv2.sfm을 사용하려면 OpenCV를 소스에서 직접 빌드해야함

```python
# mast3r 설치
conda create -n mast3r python=3.11 cmake=3.14.0 -y
conda activate mast3r 
pip install "numpy<2.0"
## cv2.sfm 직접 빌드하여 설치
...
## mast34 설치
conda install pytorch torchvision pytorch-cuda=12.1 -c pytorch -c nvidia  # cuda 12.1로 재설치
cd submodules/mast3r
pip install -r requirements.txt
pip install -r dust3r/requirements.txt
pip install -r dust3r/requirements_optional.txt
## opencv 관련 라이브러리 제거
pip uninstall -y opencv-python opencv-python-headless

## compile and install ASMK
pip install cython

cd submodules/asmk/cython/
cythonize *.pyx
cd ..
conda install -c conda-forge faiss-gpu # faiss-gpu, containing both CPU and GPU indices, is available on Linux (x86-64 only) for CUDA 11.4 and 12.1 / For FRM, MASt3R pipeline internally uses Faiss library to store correspondences.
pip install .  # or python3 setup.py build_ext --inplace
cd ..


# DKM 설치
pip install submodules/DKM 
# DKM 설치시 같이 깔린 opencv 라이브러리 제거
pip uninstall -y opencv-python opencv-python-headless
```

## Dense Matching Algorithm
- [DUSt3R](https://github.com/naver/dust3r)
  - DUSt3R 기본 모델로 pixel별 3D point를 예측했었습니다. 이 관계를 기반으로 focal length도 예측할 수 있습니다.
- [MASt3R](https://github.com/naver/mast3r)
  - [MASt3R and MASt3R-SfM Explanation: Image Matching and 3D Reconstruction Results](https://learnopencv.com/mast3r-sfm-grounding-image-matching-3d/?utm_source=chatgpt.com)
  - In MASt3R, a pixel i in image 1 and a pixel j in image 2 are considered as true match if they correspond to the same ground truth 3D point. i.e. Each local descriptor in a image matches at max only a single descriptor in the other image. The network is trained to learn such descriptors while penalizing non-matching feature descriptors using InfoNCE loss which is much more effective than a simple 3D regression loss, as used in DUSt3R.
  - MASt3R effectively handles extreme viewpoint differences upto 180 degrees-scenarios that can be sometimes ambiguous to humans. This remarkable performance is primarily attributed to MASt3R and DUSt3R’s 3D scene understanding and image matching techniques.
  <p align="center">
    <img src="https://github.com/user-attachments/assets/58dfdbfd-2c49-4a7c-bd21-ff1b696b7f59" width="600"/>
  </p>
  <p align="center"><em>MASt3R performance on Hard Cases</em></p>
- **Key Takeaways**
  - DUSt3R and MASt3R have excellent 3D scene understanding and performs in the wild zero shot. From the predicted 3D geometry focal length can be recovered making these models as a standalone and go to methods for 3D scene reconstruction and pose estimation. **Their success lies in firmly rooting image matching and finding correspondences as 3D in nature.** MASt3R predicts 3D correspondences, even in regions where there aren’t much camera motion or for neatly opposing view of the scene.
  - DUSt3R과 MASt3R의 성공은 이미지 매칭과 대응점 찾기를 본질적으로 3D 문제로 단단히 정립한 데에 있습니다. 
  - MASt3R는 카메라 움직임이 거의 없는 영역이나 장면의 정반대 시점에서도 3D 대응점을 예측할 수 있습니다.

- [DKM](https://github.com/Parskatt/DKM)

### 기존 Image Matching의 문제점 
전통적인 이미지 매칭 기법은 일반적으로 세 단계로 구성됩니다:
- (1) 키포인트 추출
- (2) 각 키포인트의 주변 영역으로부터 지역적으로 불변하는 descriptor를 추출
- (3) Feaeture Space에서 descriptor 간 거리 비교를 통해 키포인트 매칭 수행

이러한 방식은 조명 변화나 시점 변화에 비교적 강인하며, 적은 수의 키포인트만으로도 밀리초 단위의 빠른 매칭이 가능합니다. 그러나 전역적인 기하학적 문맥(geometric context)을 고려하지 않기 때문에, 반복 패턴이나 저텍스처 영역에서는 오차가 발생하기 쉽습니다.

일반적으로 Image Matching은 2D문제로 다뤄지고 있었습니다. 반면 DUSt3R에서는 Transformer기반으로 두 이미지의 pixel과 3D pointmap의 correspondence 예측을 통해 3D공간상에서 Image Matching 문제를 풀었습니다.
**하지만 DUSt3R이 3D Reconstruction 목적으로 만들어졌기에, 시점 변화엔 강인하지만 Image Matching에선 상대적으로 부정확합니다. MASt3R에서는 DUSt3R을 활용하여 Image Matching에 특화하는 방법에 관해 다룹니다.**

  <p align="center">
    <img src="https://github.com/user-attachments/assets/5ec51bfc-85d5-4bb6-b0ad-0ebffab5d600" width="600"/>
  </p>
  <p align="center"><em>MASt3R performance on extreme viewpoint differences</em></p>

위 그림은 MASt3R에서 가져왔습니다. 2개 입력 이미지의 공통 영역이 아주 적음에도 불구하고, 2D문제가 아니라 3D문제로 풀었기 때문에, Image Matching이 잘 된다는 것을 보여주는 이미지인 것 같습니다. 


## 🔍 용어 정리: "Dense Reconstruction"
Dense reconstruction은 일반적으로 MVS (Multi-View Stereo) 를 통해 장면의 표면을 조밀한 3D 포인트 클라우드 또는 mesh로 복원하는 것을 의미합니다.
이때는 triangulated sparse points가 아닌, 픽셀 단위로 대응점을 찾고 깊이 정보를 추정하여 수십만~수백만 개의 3D 점을 생성합니다.
→ COLMAP에서도 MVS를 사용한 patch_match_stereo, stereo_fusion 이후가 진짜 dense reconstruction입니다.

### 흔한 혼동: Dense feature 사용 = dense reconstruction?
어떤 연구나 구현에서는 dense feature matcher (e.g., LoFTR)만 사용해도 이를 "dense reconstruction"이라 부르는 경우가 있습니다. 하지만 엄밀히 보면 이건: dense correspondences 기반의 SfM 또는 dense SfM 이라고 부르는 게 더 정확합니다.

## 🔍 용어 정리: Map-free relocalization
Map-free relocalization은 기존의 지도 없이 주어진 이미지에서 카메라의 위치 및 방향(6DoF pose) 을 추정하는 문제입니다.
즉, SLAM이나 SfM으로 미리 구축된 3D map 없이, 오직 이미지 쌍(또는 다중 이미지)만으로 상대 위치를 추정합니다.

#### 🧠 Map-free relocalization은은 왜 어려운가?
- 지도 없이 절대 위치나 스케일을 알 수 없음
- 이미지 간 대응점만으로 metric scale의 정확한 위치 추정이 어려움
- 다양한 시점 변화(viewpoint change) 에 강인해야 함

#### MASt3R -> dense image matching & metric scale 3D pose estimation
- MASt3R는 dense image matching과 metric-scale 3D 추정을 동시에 달성하여, map 없이도 정확한 pose estimation이 가능하도록 설계되었습니다.
- 즉, 3D geometry 없이도 이미지 간의 대응점과 카메라 포즈를 추정할 수 있어 Map-free relocalization에 적합합니다.

#### 🧭 기존 relocalization과의 차이
- Map-based Relocalization:	기존 3D 모델 또는 포인트 클라우드 필요
- Map-free Relocalization:	사전 지도 없이 이미지 간 대응만으로 포즈 추정

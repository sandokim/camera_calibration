# Multicam captures
build/Desktop_Qt_6_9_0_MSVC2022_64bit-Debug/multicam.exe 실행 후 캡처

# 가상환경 설치 / GS
# CUDA 11.4 설치 / CUDA 11.4와 호환되는 torch 없음
# CUDA 11.4 보다 낮은 버전의 CUDA 11.3와 호환되는 torch로 설치

conda activate GS
pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 torchaudio==0.12.1 --extra-index-url https://download.pytorch.org/whl/cu113 --timeout 300


# COLMAP 설치 (https://github.com/colmap/colmap/releases)
Windows cuda (COLMAP 3.11.1 설치)
COLMAP 폴더 위치를 C:\Users\Kang\colmap-x64-windows-cuda로 옮기고, 시스템 환경변수에 다음 추가
C:\Users\Kang\colmap-x64-windows-cuda\bin


# gaussian-splatting/convert.py 실행 -> undistortion 수행
<location>
|---input
    |---<image 0>
    |---<image 1>
    |---...

If you have COLMAP and ImageMagick on your system path, you can simply run

python convert.py -s <location> [--resize] #If not resizing, ImageMagick is not needed

Once done, <location> will contain the expected COLMAP data set structure with undistorted, resized input images, in addition to your original images and some temporary (distorted) data in the directory distorted.

python convert.py -s C:/Users/Kang/Desktop/multicam/build/Desktop_Qt_6_9_0_MSVC2022_64bit-Release/captures


# 만약 COLMAP 데이터 구조를 가졌지만 아직 undistortion 되지 않은 이미지들이라면 아래를 수행하면 됌
If you have your own COLMAP dataset without undistortion (e.g., using OPENCV camera), you can try to just run the last part of the script: Put the images in input and the COLMAP info in a subdirectory distorted:

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
Then run

python convert.py -s <location> --skip_matching [--resize] #If not resizing, ImageMagick is not needed

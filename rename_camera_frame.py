import os

def rename_and_replace_files(source_directory):
    # 파일을 처리할 때 사용할 시작 번호
    sequence_number = 0

    for filename in sorted(os.listdir(source_directory)):
        if filename.startswith("Camera MV-SUA630C"):
            # 파일명 분석 및 필요 정보 추출
            parts = filename.split("#")[1]
            camera_id, _ = parts.split("-")[:2]  # 여기서는 camera_id만 사용하며, 기존 sequence는 사용하지 않음

            # 새로운 파일명 생성
            new_filename = f"{int(camera_id):03d}_{sequence_number:02d}.jpg"
            sequence_number += 1  # 다음 파일을 위해 시퀀스 번호 증가

            # 원본 파일 경로와 새로운 파일 경로 설정
            source_path = os.path.join(source_directory, filename)
            new_path = os.path.join(source_directory, new_filename)

            # 파일 이름 변경 (이 과정에서 원본 파일은 새로운 이름으로 대체됨)
            os.rename(source_path, new_path)
            print(f"Renamed '{filename}' to '{new_filename}'")

# 사용 예시
basedir = "C:/Users/MNL/KHS/camera_calibration/dataset"
pattern_path = "5th_pattern@180deg"
deg_0_distorted_path = os.path.join(basedir, pattern_path, "0deg_Distorted")

rename_and_replace_files(deg_0_distorted_path)

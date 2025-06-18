#include "multicam.h"
#include "./ui_multicam.h"

#include <QKeyEvent>
#include <QDir>
#include <QDateTime>
#include <QDebug>

#include <opencv2/opencv.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/imgcodecs.hpp>

#include <future>

multicam::multicam(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::multicam)
{
    ui->setupUi(this);
    timer = new QTimer(this);

    // QLabel 포인터 등록 - UI objectName과 정확히 일치해야 함
    cameraLabels = {
        ui->camera0,
        ui->camera1,
        ui->camera2,
        ui->camera3,
        // ui->camera4,
        // ui->camera5,
        // ui->camera6,
        // ui->camera7
    };

    initCameras();

    connect(timer, &QTimer::timeout, this, &multicam::updateFrames);
    timer->start(33);  // 약 30fps

    // 🔽 이 줄을 추가
    connect(ui->Capture, &QPushButton::clicked, this, &multicam::saveFrames);
}

multicam::~multicam()
{
    delete ui;
    for (auto &cap : captures)
        cap.release();
}

void multicam::initCameras()
{
    qDebug() << "[INFO] 병렬 카메라 초기화 시작";

    std::vector<std::future<std::pair<int, cv::VideoCapture>>> futures;

    for (int i = 0; i < cameraCount; ++i) {
        futures.push_back(std::async(std::launch::async, [i]() {
            cv::VideoCapture cap(i, cv::CAP_ANY);
            if (cap.isOpened()) {
                cap.set(cv::CAP_PROP_FRAME_WIDTH, 960);
                cap.set(cv::CAP_PROP_FRAME_HEIGHT, 540);
                return std::make_pair(i, std::move(cap));
            } else {
                return std::make_pair(i, cv::VideoCapture());
            }
        }));
    }

    for (auto& fut : futures) {
        auto [index, cap] = fut.get();
        if (cap.isOpened()) {
            captures.push_back(std::move(cap));
            frames.emplace_back();
            qDebug() << "[OK] 카메라" << index << "열림 (스레드)";
        } else {
            qWarning() << "[ERROR] 카메라" << index << "열기 실패 (스레드)";
        }
    }

    if (captures.empty()) {
        qWarning() << "[FATAL] 사용 가능한 카메라 없음. 프로그램 실행 불가 가능성 있음.";
    }
}

void multicam::updateFrames()
{
    static int frameCount = 0;

    for (int i = 0; i < captures.size(); ++i) {
        captures[i] >> frames[i];

        if (frames[i].empty()) {
            qWarning() << "[WARNING] 카메라" << i << "프레임 비어 있음";
            continue;
        }

        QImage img = matToQImage(frames[i]);
        cameraLabels[i]->setPixmap(QPixmap::fromImage(img).scaled(
            cameraLabels[i]->size(),
            Qt::KeepAspectRatio,
            Qt::SmoothTransformation
            ));

        if (++frameCount % 30 == 0) {
            qDebug() << "[INFO] 카메라" << i << "프레임 업데이트 완료";
        }
    }
}

void multicam::keyPressEvent(QKeyEvent *event)
{
    if (event->key() == Qt::Key_S) {
        qDebug() << "[ACTION] 'S' 키 입력 - 프레임 저장 중...";
        saveFrames();
    }
}

void multicam::saveFrames()
{
    QString timestamp = QDateTime::currentDateTime().toString("yyyyMMdd_HHmmss");

    // 공통 input 디렉토리 생성
    QString inputDirPath = "./scene/myface/images/input";
    QDir().mkpath(inputDirPath);

    for (int i = 0; i < frames.size(); ++i) {
        // 개별 카메라 폴더 경로 생성
        QString camDirPath = QString("./scene/myface/images/cam%1").arg(i);
        QDir().mkpath(camDirPath);

        // 파일명 정의
        QString fileName = QString("cam%1_%2.jpg").arg(i).arg(timestamp);

        // 경로 1: cam 개별 폴더
        QString camFilePath = QString("%1/%2").arg(camDirPath, fileName);
        bool successCam = cv::imwrite(camFilePath.toStdString(), frames[i]);

        if (successCam) {
            qDebug() << "[SAVE] 개별 저장 완료:" << camFilePath;
        } else {
            qWarning() << "[ERROR] 개별 저장 실패:" << camFilePath;
        }

        // // 경로 2: input 공통 폴더 (파일명: camX_타임스탬프.jpg)
        // QString inputFilePath = QString("%1/cam%2_%3.jpg")
        //                             .arg(inputDirPath)
        //                             .arg(i)
        //                             .arg(timestamp);
        // bool successInput = cv::imwrite(inputFilePath.toStdString(), frames[i]);

        // if (successInput) {
        //     qDebug() << "[SAVE] input 저장 완료:" << inputFilePath;
        // } else {
        //     qWarning() << "[ERROR] input 저장 실패:" << inputFilePath;
        // }
    }
}

QImage multicam::matToQImage(const cv::Mat &mat)
{
    if (mat.empty()) return QImage();

    if (mat.type() == CV_8UC3) {
        return QImage(mat.data, mat.cols, mat.rows, mat.step, QImage::Format_BGR888).copy();
    } else if (mat.type() == CV_8UC1) {
        return QImage(mat.data, mat.cols, mat.rows, mat.step, QImage::Format_Grayscale8).copy();
    } else {
        qWarning() << "[ERROR] 지원되지 않는 이미지 타입:" << mat.type();
        return QImage();
    }
}

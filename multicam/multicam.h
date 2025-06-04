#ifndef MULTICAM_H
#define MULTICAM_H

#include <QMainWindow>
#include <QTimer>
#include <QLabel>
#include <opencv2/core.hpp>
#include <opencv2/videoio.hpp>

QT_BEGIN_NAMESPACE
namespace Ui {
class multicam;
}
QT_END_NAMESPACE

class multicam : public QMainWindow
{
    Q_OBJECT

public:
    explicit multicam(QWidget *parent = nullptr);
    ~multicam();

protected:
    void keyPressEvent(QKeyEvent *event) override;

private slots:
    void updateFrames();

private:
    Ui::multicam *ui;
    QTimer *timer;
    int cameraCount = 4;  // 향후 8로 확장 가능

    std::vector<cv::VideoCapture> captures;
    std::vector<cv::Mat> frames;
    std::vector<QLabel*> cameraLabels;

    void initCameras();
    void saveFrames();
    QImage matToQImage(const cv::Mat &mat);
};

#endif // MULTICAM_H

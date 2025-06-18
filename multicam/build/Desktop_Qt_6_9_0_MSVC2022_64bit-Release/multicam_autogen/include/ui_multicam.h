/********************************************************************************
** Form generated from reading UI file 'multicam.ui'
**
** Created by: Qt User Interface Compiler version 6.9.0
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_MULTICAM_H
#define UI_MULTICAM_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QHBoxLayout>
#include <QtWidgets/QLabel>
#include <QtWidgets/QMainWindow>
#include <QtWidgets/QMenuBar>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QStatusBar>
#include <QtWidgets/QVBoxLayout>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_multicam
{
public:
    QWidget *centralwidget;
    QWidget *layoutWidget;
    QVBoxLayout *verticalLayout;
    QHBoxLayout *horizontalLayout;
    QLabel *camera0;
    QLabel *camera1;
    QLabel *camera2;
    QLabel *camera3;
    QHBoxLayout *horizontalLayout_2;
    QLabel *camera4;
    QLabel *camera5;
    QLabel *camera6;
    QLabel *camera7;
    QPushButton *Capture;
    QMenuBar *menubar;
    QStatusBar *statusbar;

    void setupUi(QMainWindow *multicam)
    {
        if (multicam->objectName().isEmpty())
            multicam->setObjectName("multicam");
        multicam->resize(1280, 720);
        centralwidget = new QWidget(multicam);
        centralwidget->setObjectName("centralwidget");
        layoutWidget = new QWidget(centralwidget);
        layoutWidget->setObjectName("layoutWidget");
        layoutWidget->setGeometry(QRect(10, 10, 991, 441));
        verticalLayout = new QVBoxLayout(layoutWidget);
        verticalLayout->setObjectName("verticalLayout");
        verticalLayout->setContentsMargins(0, 0, 0, 0);
        horizontalLayout = new QHBoxLayout();
        horizontalLayout->setObjectName("horizontalLayout");
        camera0 = new QLabel(layoutWidget);
        camera0->setObjectName("camera0");
        QFont font;
        font.setFamilies({QString::fromUtf8("Arial")});
        font.setPointSize(14);
        camera0->setFont(font);
        camera0->setAlignment(Qt::AlignmentFlag::AlignCenter);

        horizontalLayout->addWidget(camera0);

        camera1 = new QLabel(layoutWidget);
        camera1->setObjectName("camera1");
        camera1->setFont(font);
        camera1->setAlignment(Qt::AlignmentFlag::AlignCenter);

        horizontalLayout->addWidget(camera1);

        camera2 = new QLabel(layoutWidget);
        camera2->setObjectName("camera2");
        camera2->setFont(font);
        camera2->setAlignment(Qt::AlignmentFlag::AlignCenter);

        horizontalLayout->addWidget(camera2);

        camera3 = new QLabel(layoutWidget);
        camera3->setObjectName("camera3");
        camera3->setFont(font);
        camera3->setAlignment(Qt::AlignmentFlag::AlignCenter);

        horizontalLayout->addWidget(camera3);


        verticalLayout->addLayout(horizontalLayout);

        horizontalLayout_2 = new QHBoxLayout();
        horizontalLayout_2->setObjectName("horizontalLayout_2");
        camera4 = new QLabel(layoutWidget);
        camera4->setObjectName("camera4");
        camera4->setFont(font);
        camera4->setAlignment(Qt::AlignmentFlag::AlignCenter);

        horizontalLayout_2->addWidget(camera4);

        camera5 = new QLabel(layoutWidget);
        camera5->setObjectName("camera5");
        camera5->setFont(font);
        camera5->setAlignment(Qt::AlignmentFlag::AlignCenter);

        horizontalLayout_2->addWidget(camera5);

        camera6 = new QLabel(layoutWidget);
        camera6->setObjectName("camera6");
        camera6->setFont(font);
        camera6->setAlignment(Qt::AlignmentFlag::AlignCenter);

        horizontalLayout_2->addWidget(camera6);

        camera7 = new QLabel(layoutWidget);
        camera7->setObjectName("camera7");
        camera7->setFont(font);
        camera7->setAlignment(Qt::AlignmentFlag::AlignCenter);

        horizontalLayout_2->addWidget(camera7);


        verticalLayout->addLayout(horizontalLayout_2);

        Capture = new QPushButton(centralwidget);
        Capture->setObjectName("Capture");
        Capture->setGeometry(QRect(10, 460, 101, 61));
        Capture->setFont(font);
        multicam->setCentralWidget(centralwidget);
        menubar = new QMenuBar(multicam);
        menubar->setObjectName("menubar");
        menubar->setGeometry(QRect(0, 0, 1280, 18));
        multicam->setMenuBar(menubar);
        statusbar = new QStatusBar(multicam);
        statusbar->setObjectName("statusbar");
        multicam->setStatusBar(statusbar);

        retranslateUi(multicam);

        QMetaObject::connectSlotsByName(multicam);
    } // setupUi

    void retranslateUi(QMainWindow *multicam)
    {
        multicam->setWindowTitle(QCoreApplication::translate("multicam", "multicam", nullptr));
        camera0->setText(QCoreApplication::translate("multicam", "camera0", nullptr));
        camera1->setText(QCoreApplication::translate("multicam", "camera1", nullptr));
        camera2->setText(QCoreApplication::translate("multicam", "camera2", nullptr));
        camera3->setText(QCoreApplication::translate("multicam", "camera3", nullptr));
        camera4->setText(QCoreApplication::translate("multicam", "camera4", nullptr));
        camera5->setText(QCoreApplication::translate("multicam", "camera5", nullptr));
        camera6->setText(QCoreApplication::translate("multicam", "camera6", nullptr));
        camera7->setText(QCoreApplication::translate("multicam", "camera7", nullptr));
        Capture->setText(QCoreApplication::translate("multicam", "Capture", nullptr));
    } // retranslateUi

};

namespace Ui {
    class multicam: public Ui_multicam {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_MULTICAM_H

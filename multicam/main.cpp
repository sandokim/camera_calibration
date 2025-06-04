#include "multicam.h"

#include <QApplication>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    multicam w;
    w.show();
    return a.exec();
}

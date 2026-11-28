#include <QApplication>
#include <QLabel>

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    QLabel window(QStringLiteral("Caneda · Qt Widgets"));
    window.setWindowTitle(QStringLiteral("Caneda"));
    window.setAlignment(Qt::AlignCenter);
    window.resize(480, 240);
    window.show();
    return app.exec();
}

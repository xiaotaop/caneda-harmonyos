#include "port.h"
#include <QtWidgets>
#include <QGenericPlugin>
#include <QTest>

namespace {
using Caneda::GraphicsItem;
using Caneda::Port;

QString verifyWiring(QMainWindow *window, QDir output, QJsonObject &record)
{
    if (auto *folder = window->findChild<QDockWidget *>("folderBrowserSidebar"))
        folder->hide();
    window->resize(1240, 800);
    window->activateWindow();
    if (!QTest::qWaitForWindowActive(window))
        return "Main window did not take focus";
    QGraphicsView *canvas = nullptr;
    QTreeView *tree = nullptr;
    QToolButton *wireButton = nullptr;
    for (auto *v : window->findChildren<QGraphicsView *>())
        if (v->isVisible() && v->inherits("Caneda::GraphicsView")) canvas = v;
    for (auto *v : window->findChildren<QTreeView *>())
        if (v->isVisible() && v->parentWidget()->inherits("Caneda::SidebarItemsBrowser")) tree = v;
    for (auto *b : window->findChildren<QToolButton *>())
        if (b->isVisible() && b->defaultAction() && b->defaultAction()->objectName() == "insertWire")
            wireButton = b;
    if (!canvas || !tree || !wireButton || !canvas->scene())
        return "Missing canvas, component panel or Wire button";
    auto items = [&](int type) {
        QList<GraphicsItem *> found;
        for (auto *item : canvas->scene()->items())
            if (item->type() == type) found.append(static_cast<GraphicsItem *>(item));
        return found;
    };
    if (!window->windowTitle().contains("d4-rc") || !items(GraphicsItem::ComponentType).isEmpty()
        || !items(GraphicsItem::WireType).isEmpty())
        return "Start with the empty d4-rc.xsch in a fresh output directory";
    auto *handle = window->windowHandle();
    auto click = [&](QWidget *widget, QPoint local) {
        if (!widget->rect().contains(local)) return false;
        const auto point = widget->mapTo(window, local);
        QTest::mouseMove(handle, point);
        QTest::mouseClick(handle, Qt::LeftButton, {}, point);
        return true;
    };
    auto clickGrid = [&](QPoint point) {
        return click(canvas->viewport(), canvas->mapFromScene(QPointF(point)));
    };
    auto place = [&](QString name, QPoint point) {
        auto *model = tree->model();
        const auto hits = model->match(model->index(0,0), Qt::DisplayRole, name, 1,
                                       Qt::MatchExactly | Qt::MatchRecursive);
        if (hits.isEmpty()) return false;
        const auto row = hits.first();
        tree->expand(row.parent().parent());
        tree->expand(row.parent());
        tree->scrollTo(row);
        QTest::qWait(200);
        if (!click(tree->viewport(), tree->visualRect(row).center()) || !clickGrid(point))
            return false;
        QTest::keyClick(handle, Qt::Key_Escape);
        return tree->currentIndex() == row;
    };
    if (!place("Resistor", {-80, 0}) || !place("Capacitor", {80, 0}))
        return "Could not place both components using the panel";
    const auto parts = items(GraphicsItem::ComponentType);
    if (parts.size() != 2 || !items(GraphicsItem::WireType).isEmpty())
        return "Expected two components and no wire before routing";
    QMap<int, Port *> pins;
    for (auto *part : parts)
        for (auto *pin : part->ports()) {
            if (pin->scenePos().y() != 0 || pin->connections()->size() != 1)
                return "Expected four initially open pins on the same row";
            pins.insert(qRound(pin->scenePos().x()), pin);
        }
    if (pins.keys() != QList<int>{-100,-60,60,100})
        return "Unexpected component terminal positions";
    if (!click(wireButton, wireButton->rect().center()) || !clickGrid({-60,0}) || !clickGrid({60,0}))
        return "Could not route the inner terminals";
    QTest::keyClick(handle, Qt::Key_Escape);
    const auto wires = items(GraphicsItem::WireType);
    if (wires.size() != 1 || wires.first()->ports().size() != 2)
        return "Expected one completed wire";
    for (auto *end : wires.first()->ports()) {
        auto *pin = pins.value(qRound(end->scenePos().x()));
        if (!pin || pin->scenePos() != end->scenePos() || pin->connections()->size() != 2 ||
            !end->connections()->contains(pin) || !pin->connections()->contains(end))
            return "Wire endpoint and component terminal did not connect to each other";
    }
    if (pins[-60]->connections()->size() != 2 || pins[60]->connections()->size() != 2 ||
        pins[-100]->connections()->size() != 1 || pins[100]->connections()->size() != 1)
        return "Expected only the two inner terminals to be wired";
    record["components"] = parts.size();
    record["wires"] = wires.size();
    record["connectedPinX"] = QJsonArray{-60,60};
    record["openPinX"] = QJsonArray{-100,100};
    QTest::keyClick(handle, Qt::Key_S, Qt::ControlModifier);
    QTest::qWait(150);
    if (!window->grab().save(output.filePath("wired.png")))
        return "Could not save the completed schematic screenshot";
    return {};
}
}

class WiringProbe : public QGenericPlugin {
    Q_OBJECT
    Q_PLUGIN_METADATA(IID QGenericPluginFactoryInterface_iid FILE "probe.json")
public:
    QObject *create(const QString &key, const QString &) override {
        const QString path = qEnvironmentVariable("CANEDA_D4_OUTPUT");
        if (key.compare("caneda_d4", Qt::CaseInsensitive) || path.isEmpty()) return nullptr;
        QSettings::setDefaultFormat(QSettings::IniFormat);
        QSettings::setPath(QSettings::IniFormat, QSettings::UserScope, QDir(path).filePath("settings"));
        auto *session = new QObject;
        QTimer::singleShot(1000, session, [path] {
            QString error = "Main window missing";
            QJsonObject record{{"platform", QGuiApplication::platformName()}, {"qt", qVersion()}};
            for (auto *widget : qApp->topLevelWidgets()) {
                auto *window = qobject_cast<QMainWindow *>(widget);
                if (window && window->isVisible()) {
                    error = verifyWiring(window, QDir(path), record);
                    break;
                }
            }
            record["error"] = error;
            const auto bytes = QJsonDocument(record).toJson();
            QFile file(QDir(path).filePath("wiring.json"));
            const bool saved = file.open(QIODevice::WriteOnly) && file.write(bytes) == bytes.size() && file.flush();
            qApp->exit(saved && error.isEmpty() ? 0 : 1);
        });
        return session;
    }
};
#include "probe.moc"

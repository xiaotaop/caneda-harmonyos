#include <QtWidgets>
#include <QGenericPlugin>
#include <QTest>

namespace {
QString checkFocus(QDir output, QJsonObject &log)
{
    QMainWindow *window = nullptr;
    for (auto *widget : qApp->topLevelWidgets())
        if (widget->isVisible() && qobject_cast<QMainWindow *>(widget))
            window = qobject_cast<QMainWindow *>(widget);
    if (!window)
        return "No visible main window";
    if (auto *folders = window->findChild<QDockWidget *>("folderBrowserSidebar"))
        folders->hide();
    window->resize(1240, 800);
    window->activateWindow();
    if (!QTest::qWaitForWindowActive(window))
        return "Main window could not take keyboard focus";
    QTreeView *tree = nullptr;
    QGraphicsView *canvas = nullptr;
    for (auto *view : window->findChildren<QGraphicsView *>())
        if (view->isVisible() && view->inherits("Caneda::GraphicsView"))
            canvas = view;
    for (auto *view : window->findChildren<QTreeView *>())
        if (view->isVisible() && view->parentWidget()->inherits("Caneda::SidebarItemsBrowser"))
            tree = view;
    if (!canvas || !canvas->scene() || !tree)
        return "Schematic canvas or component panel missing";
    auto *search = tree->parentWidget()->findChild<QLineEdit *>();
    if (!search || !search->isVisible())
        return "Component search field missing";

    auto *handle = window->windowHandle();
    auto click = [&](QWidget *widget, QPoint position) {
        const QPoint point = widget->mapTo(window, position);
        QTest::mouseMove(handle, point);
        QTest::mouseClick(handle, Qt::LeftButton, {}, point);
    };
    auto type = [&](const QByteArray &text) {
        for (char letter : text)
            QTest::keyClick(handle, letter);
    };
    auto findResult = [&](const QString &name) {
        auto *model = tree->model();
        return model->match(model->index(0, 0), Qt::DisplayRole, name, 1,
                            Qt::MatchExactly | Qt::MatchRecursive);
    };
    auto componentPositions = [&]() {
        QList<QPointF> positions;
        // Component::Type from src/graphicsitem.h.
        for (auto *item : canvas->scene()->items())
            if (item->type() == ((1 << 30) | (1 << 29)))
                positions.append(item->scenePos());
        return positions;
    };
    if (!componentPositions().isEmpty())
        return "Start with an empty schematic";
    qInfo() << "Checking component search";
    click(search, search->rect().center());
    type("capacitor");
    log["searchText"] = search->text();
    if (!search->hasFocus() || search->text() != "capacitor" ||
        findResult("Capacitor").isEmpty() || !findResult("Resistor").isEmpty())
        return "Search did not receive typing or filter the result tree";
    qInfo() << "Navigating filtered results";
    QTest::keyClick(handle, Qt::Key_Down);
    if (!tree->hasFocus())
        return "Down did not transfer focus to the results";
    // Navigate visible rows by keyboard, as a user would.
    while (tree->currentIndex().isValid() && tree->currentIndex().data() != "Capacitor") {
        const auto before = tree->currentIndex();
        QTest::keyClick(handle, Qt::Key_Down);
        if (tree->currentIndex() == before)
            break;
    }
    log["keyboardSelection"] = tree->currentIndex().data().toString();
    if (tree->currentIndex().data() != "Capacitor")
        return "Capacitor was not reachable by keyboard";
    if (!window->grab().save(output.filePath("01-search.png")))
        return "Could not capture search results";
    QTest::keyClick(handle, Qt::Key_Return);
    const QPointF gridPoint(40, 30);
    const QPoint target = canvas->mapFromScene(gridPoint);
    if (!canvas->viewport()->rect().contains(target))
        return "Target outside viewport";
    click(canvas->viewport(), target);
    QTest::keyClick(handle, Qt::Key_Escape);
    const auto placed = componentPositions();
    log["componentCountAfterEsc"] = placed.size();
    log["canvasFocusAfterEsc"] = canvas->hasFocus();
    if (!canvas->hasFocus() || placed != QList<QPointF>{gridPoint})
        return "Expected canvas focus and one component at (40,30) after Esc";
    log["componentScenePosition"] = QJsonArray{placed.first().x(), placed.first().y()};
    click(search, search->rect().center());
    QTest::keyClick(handle, Qt::Key_A, Qt::ControlModifier);
    type("resistor");
    log["secondSearchText"] = search->text();
    log["searchFocusAfterReturn"] = search->hasFocus();
    if (!search->hasFocus() || search->text() != "resistor" ||
        findResult("Resistor").isEmpty() || !findResult("Capacitor").isEmpty() ||
        componentPositions() != placed)
        return "Returning to search changed the schematic or failed to refilter";
    if (!window->grab().save(output.filePath("02-return.png")))
        return "Could not capture the final canvas and panel";
    return {};
}
}

class CanedaFocusProbe : public QGenericPlugin {
    Q_OBJECT
    Q_PLUGIN_METADATA(IID QGenericPluginFactoryInterface_iid FILE "probe.json")
public:
    QObject *create(const QString &key, const QString &) override {
        const QString path = qEnvironmentVariable("CANEDA_D3_OUTPUT");
        if (key.compare("caneda_d3", Qt::CaseInsensitive) || path.isEmpty())
            return nullptr;
        QSettings::setDefaultFormat(QSettings::IniFormat);
        QSettings::setPath(QSettings::IniFormat, QSettings::UserScope, QDir(path).filePath("settings"));
        auto *session = new QObject;
        qInfo() << "Starting D3 focus probe";
        QTimer::singleShot(1000, session, [path] {
            qInfo() << "Checking the active schematic";
            QJsonObject log{{"qt", qVersion()}, {"platform", QGuiApplication::platformName()},
                            {"version", qApp->applicationVersion()}};
            const QString error = checkFocus(QDir(path), log);
            log["error"] = error;
            const auto bytes = QJsonDocument(log).toJson();
            QFile file(QDir(path).filePath("focus.json"));
            const bool saved = file.open(QIODevice::WriteOnly) &&
                               file.write(bytes) == bytes.size() && file.flush();
            qApp->exit(saved && error.isEmpty() ? 0 : 1);
        });
        return session;
    }
};
#include "probe.moc"

#include <QtWidgets>
#include <QGenericPlugin>
#include <QSignalSpy>
#include <QTest>
#include <QWindow>

namespace {
QJsonArray xy(QPointF p) { return {p.x(), p.y()}; }

class Check : public QObject {
public:
    QDir out{qEnvironmentVariable("CANEDA_D2_OUTPUT")};
    QJsonObject record;
    QMainWindow *window = nullptr;

    void finish(QString error = {}) {
        record["error"] = error;
        record["qt"] = qVersion();
        record["platform"] = QGuiApplication::platformName();
        record["version"] = qApp->applicationVersion();
        QFile file(out.filePath("interaction.json"));
        bool saved = file.open(QIODevice::WriteOnly)
            && file.write(QJsonDocument(record).toJson()) > 0 && file.flush();
        qApp->exit(saved && error.isEmpty() ? 0 : 1);
    }

    void run() {
        for (auto *w : qApp->topLevelWidgets())
            if (w->isVisible() && qobject_cast<QMainWindow *>(w))
                window = qobject_cast<QMainWindow *>(w);
        if (!window) return finish("Main window missing");
        if (auto *folder = window->findChild<QDockWidget *>("folderBrowserSidebar")) folder->hide();
        window->resize(1240, 800);
        window->activateWindow();
        QTest::qWait(300);
        QGraphicsView *canvas = nullptr;
        for (auto *v : window->findChildren<QGraphicsView *>())
            if (v->isVisible() && v->inherits("Caneda::GraphicsView")) canvas = v;
        if (!canvas || !canvas->scene()) return finish("Canvas missing");
        record["os"] = QSysInfo::prettyProductName();
        record["architecture"] = QSysInfo::currentCpuArchitecture();
        record["title"] = window->windowTitle();
        record["canvas"] = canvas->metaObject()->className();
        record["devicePixelRatio"] = window->devicePixelRatioF();
        for (auto *tree : window->findChildren<QTreeView *>()) {
            if (!tree->isVisible() || !tree->model() ||
                !tree->parentWidget()->inherits("Caneda::SidebarItemsBrowser")) continue;
            auto *model = tree->model();
            auto hits = model->match(model->index(0,0), Qt::DisplayRole, "Resistor", 1,
                                     Qt::MatchExactly | Qt::MatchRecursive);
            if (hits.isEmpty()) continue;
            auto index = hits.first();
            tree->expand(index.parent().parent());
            tree->expand(index.parent());
            tree->scrollTo(index);
            QTest::qWait(150);
            auto *handle = window->windowHandle();
            auto click = [&](QWidget *widget, QPoint point) {
                auto pos = widget->mapTo(window, point);
                QTest::mouseMove(handle, pos);
                QTest::mouseClick(handle, Qt::LeftButton, {}, pos);
                QTest::qWait(80);
            };
            click(tree->viewport(), tree->visualRect(index).center());
            record["panelSelection"] = tree->currentIndex().data().toString();
            record["panelFocus"] = tree->hasFocus();
            if (!window->grab().save(out.filePath("01-panel.png"))) return finish("Panel capture failed");
            auto *vp = canvas->viewport();
            auto target = canvas->mapFromScene(QPointF(40, 30));
            if (!vp->rect().contains(target)) return finish("Target outside canvas");
            QSignalSpy moves(canvas, SIGNAL(cursorPositionChanged(QString)));
            click(vp, target);
            record["viewportClick"] = xy(target);
            record["sceneClick"] = xy(canvas->mapToScene(target));
            record["cursorReadout"] = moves.isEmpty() ? QString() : moves.last().first().toString();
            record["canvasFocusAfterPlacement"] = canvas->hasFocus();
            QTest::keyClick(handle, Qt::Key_Escape);
            QTest::qWait(100);
            // Component::Type is PATTERN(GraphicsItemType, 1) in graphicsitem.h.
            const int componentType = (1 << 30) | (1 << 29);
            QList<QGraphicsItem *> parts;
            for (auto *item : canvas->scene()->items())
                if (item->type() == componentType) parts.append(item);
            record["placedCount"] = parts.size();
            if (parts.size() != 1) return finish("Expected one placed component after Escape");
            auto *part = parts.first();
            record["componentPosition"] = xy(part->scenePos());
            // Clear selection on the blank canvas, then hit the resistor body.
            click(vp, target + QPoint(80,60));
            record["clearSelection"] = canvas->scene()->selectedItems().isEmpty();
            click(vp, target);
            record["selectedComponent"] = part->isSelected();
            record["canvasFocusAfterSelection"] = canvas->hasFocus();
            if (!window->grab().save(out.filePath("02-selected.png"))) return finish("Canvas capture failed");
            if (tree->currentIndex() != index || !record["panelFocus"].toBool()
                || !record["canvasFocusAfterPlacement"].toBool() || !canvas->hasFocus()
                || !record["clearSelection"].toBool() || !part->isSelected()
                || part->scenePos() != QPointF(40,30)
                || record["cursorReadout"].toString() != "40 : 30")
                return finish("Interaction assertions failed");
            return finish();
        }
        finish("Resistor missing");
    }
};
}

class CanedaDesktopPlugin : public QGenericPlugin {
    Q_OBJECT
    Q_PLUGIN_METADATA(IID QGenericPluginFactoryInterface_iid FILE "probe.json")
public:
    QObject *create(const QString &name, const QString &) override {
        if (name.compare("caneda_d2", Qt::CaseInsensitive)
            || qEnvironmentVariableIsEmpty("CANEDA_D2_OUTPUT")) return nullptr;
        auto *check = new Check;
        QSettings::setDefaultFormat(QSettings::IniFormat);
        QSettings::setPath(QSettings::IniFormat, QSettings::UserScope, check->out.filePath("settings"));
        QTimer::singleShot(1000, check, [check]{ check->run(); });
        return check;
    }
};
#include "probe.moc"

import { UIAbility } from '@kit.AbilityKit';
import { window } from '@kit.ArkUI';
import { fileIo as fs } from '@kit.CoreFileKit';
import { hilog } from '@kit.PerformanceAnalysisKit';
import { run } from 'libngspice_probe.so';

export default class EntryAbility extends UIAbility {
  onWindowStageCreate(stage: window.WindowStage): void {
    try {
      stage.loadContent('pages/Index');
      const name: string = 'rc-' + Date.now().toString();
      const dir: string = this.context.filesDir + '/' + name;
      fs.mkdirSync(dir);
      this.copyResource('rc-step.cir', dir + '/rc-step.cir');
      this.copyResource('ngspice.bin', dir + '/ngspice');
      const result: string = run(dir);
      AppStorage.setOrCreate('result', result);
      hilog.warn(0x0000, 'CanedaD3', '%{public}s %{public}s', name, result);
    } catch (error) {
      hilog.error(0x0000, 'CanedaD3', 'probe failed: %{public}s', JSON.stringify(error));
    }
  }

  private copyResource(name: string, destination: string): void {
    const bytes: Uint8Array = this.context.resourceManager.getRawFileContentSync(name);
    const file = fs.openSync(destination, fs.OpenMode.CREATE | fs.OpenMode.WRITE_ONLY);
    try {
      const written: number = fs.writeSync(file.fd, bytes.buffer);
      if (written !== bytes.byteLength) {
        throw new Error('Short resource write for ' + name);
      }
    } finally {
      fs.closeSync(file);
    }
  }
}

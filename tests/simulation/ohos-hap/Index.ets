@Entry
@Component
struct Index {
  @StorageLink('result') result: string = 'Running RC probe';
  build() {
    Column() {
      Text(this.result)
    }.width('100%').height('100%').justifyContent(FlexAlign.Center)
  }
}

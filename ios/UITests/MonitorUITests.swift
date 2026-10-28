import XCTest
final class MonitorUITests:XCTestCase {
 func testNativeScreensRenderAndFiltersOpen(){
  let app=XCUIApplication();app.launchArguments=["-ui-testing"];app.launch()
  XCTAssertTrue(app.staticTexts["رصد السياحة الأردنية"].waitForExistence(timeout:15))
  XCTAssertTrue(app.buttons["filters-button"].isHittable);app.buttons["filters-button"].tap()
  XCTAssertTrue(app.buttons["filters-done"].waitForExistence(timeout:5));app.buttons["filters-done"].tap()
  app.tabBars.buttons["السوشال ميديا"].tap()
  XCTAssertTrue(app.staticTexts["اتصال المنصات"].waitForExistence(timeout:5))
  XCTAssertTrue(app.staticTexts["Facebook"].exists)
  app.tabBars.buttons["المصادر"].tap()
  XCTAssertTrue(app.buttons["places-link"].exists || app.descendants(matching:.any)["places-link"].exists)
  let image=XCTAttachment(screenshot:app.screenshot());image.name="Native iPhone UI";image.lifetime = .keepAlways;add(image)
 }
}

import XCTest
@testable import MediaMonitor
final class MonitorTests:XCTestCase {
 func row(_ date:String)->Article{Article(id:"test",title:"السياحة في الأردن",source:"Test",url:"https://example.com",published:date)}
 func testAmmanCalendarAndRollingWindows(){
  let now=Dates.parse("2026-10-28T08:00:00+03:00")!
  XCTAssertTrue(Period.yesterday.contains(row("2026-10-27T23:59:59+03:00"),now:now))
  XCTAssertFalse(Period.yesterday.contains(row("2026-10-28T00:00:00+03:00"),now:now))
  XCTAssertTrue(Period.three.contains(row("2026-10-28T05:00:00+03:00"),now:now))
  XCTAssertFalse(Period.three.contains(row("2026-10-28T04:59:59+03:00"),now:now))
  XCTAssertFalse(Period.today.contains(row(""),now:now))
  XCTAssertFalse(Period.today.contains(row("2026-10-29T05:00:00+03:00"),now:now))
  XCTAssertTrue(Dates.retained(row("2026-10-24T08:00:00+03:00"),now:now))
  XCTAssertFalse(Dates.retained(row("2026-10-24T07:59:59+03:00"),now:now))
 }
 func testCountryDisambiguation(){
  func classify(_ text:String)->String{TextRules.analyze(Article(id:text,title:text,source:"Test",url:"https://example.com",published:""),places:[]).relevance}
  XCTAssertEqual(classify("Michael Jordan visits Egypt hotel"),"مستبعد")
  XCTAssertEqual(classify("افتتاح فندق في القاهرة"),"مستبعد")
  XCTAssertEqual(classify("ارتفاع السياحة في الأردن"),"مباشر")
  XCTAssertEqual(classify("ترميم قلعة الكرك"),"غير مباشر")
 }
 func testDirectoryCompleteAndBilingual()throws{
  let directory=try XCTUnwrap(PlaceDirectory.bundled())
  XCTAssertEqual(directory.locality_count,958)
  XCTAssertEqual(Set(directory.items.map(\.governorate)).count,12)
  XCTAssertEqual(Set(directory.items.map(\.id)).count,directory.items.count)
  XCTAssertTrue(directory.items.allSatisfy{!$0.ar.isEmpty && !$0.en.isEmpty})
 }
 func testBodyOnlyKeywordAndUnknownDate(){
  var r=Article(id:"body",title:"اجتماع",source:"Test",url:"https://example.com",published:"",discovered:ISO8601DateFormatter().string(from:Date()),body:"حضر وزير السياحة عماد حجازين الاجتماع")
  r=TextRules.analyze(r,places:[]);XCTAssertTrue(r._matched_keywords?.contains(Filters.keywords[2])==true)
  var f=Filters();f.keyword=Filters.keywords[2];XCTAssertTrue(f.matches(r));f.period = .today;XCTAssertFalse(f.matches(r))
 }
}

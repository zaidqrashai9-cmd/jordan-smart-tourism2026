import Foundation

struct Article: Codable, Identifiable, Hashable {
 var id: String
 var title: String
 var source: String
 var url: String
 var published: String
 var discovered: String?
 var summary: String?
 var body: String?
 var article_url: String?
 var _relevance: String?
 var _relevance_reason: String?
 var _impact: [String]?
 var _language: String?
 var _places: [String]?
 var _matched_keywords: [String]?
 var text_scope: String?
 var platform: String?
 var account: String?
 var manual: Bool?
 var date: Date? { Dates.parse(published) }
 var link: URL? { [article_url, Optional(url)].compactMap { $0 }.compactMap(URL.init(string:)).first { $0.scheme == "https" } }
 var evidence: String { [title,summary ?? "",body ?? ""].joined(separator:" ") }
 var language: String { _language ?? (title.unicodeScalars.filter { (0x0600...0x06ff).contains($0.value) }.count > title.filter(\.isASCII).count / 2 ? "AR" : "EN") }
 var relevance: String { _relevance ?? "للمراجعة" }
 var sentiment: String { _impact?.first ?? "يحتاج مراجعة" }
 var publisherRegion:String {
  let publisher=TextRules.norm(source)
  let local=["بترا","عمون","المملكة","الدستور","الغد","الرأي","جفرا","مدار الساعة","petra","jordan times","al rai","ammon","almamlaka"]
  let global=["reuters","bbc","cnn","euronews","eturbonews","travel and tour world","fast company","el pais","elpais","the guardian","france 24","al jazeera"]
  if local.contains(where:publisher.contains){return "أردنية"}
  if global.contains(where:publisher.contains){return "دولية"}
  if let host=URL(string:article_url ?? url)?.host,host.hasSuffix(".jo"){return "أردنية"}
  return "غير مصنف"
 }
 var shareText: String { "\(title)\n\nالمصدر: \(source)\n\(link?.absoluteString ?? url)" }
}
struct SourceStatus: Codable, Identifiable {
 var query: String;var count: Int;var error: String?;var provider: String?
 var id: String { query }
}
struct SocialStatus: Codable, Identifiable {
 var platform: String;var connected: Bool;var count: Int;var message: String;var checked: String?
 var id: String { platform }
}
struct LocalitySummary: Codable { var count: Int;var governorates: Int;var source: String;var year: Int }
struct Feed: Codable {
 var items: [Article]
 var sources: [SourceStatus]?
 var updated: String?
 var last_success: String?
 var new_items: Int?
 var cursor: Int?
 var total_queries: Int?
 var checked_queries: Int?
 var last_check_successful: Bool?
 var schedule: String?
 var localities: LocalitySummary?
 var social_items: [Article]?
 var social_sources: [SocialStatus]?
 static let empty = Feed(items: [])
}
struct Place: Codable,Identifiable {
 var id:String;var ar:String;var en:String;var governorate:String;var governorate_en:String
 var district:String;var district_en:String;var subdistrict:String;var type:String
 var aliases_ar:[String];var aliases_en:[String];var english_status:String
}
struct PlaceDirectory: Codable {
 var source:String;var source_name:String;var source_year:Int;var retrieved:String
 var locality_count:Int;var governorate_count:Int;var missing_english:Int;var completeness:String;var items:[Place]
 static func bundled() -> PlaceDirectory? {
  guard let u=Bundle.main.url(forResource:"localities",withExtension:"json"),let b=try? Data(contentsOf:u) else{return nil}
  return try? JSONDecoder().decode(PlaceDirectory.self,from:b)
 }
}
enum Dates {
 static let zone=TimeZone(identifier:"Asia/Amman")!
 private static let lock=NSLock()
 private static var cache:[String:Date]=[:]
 private static var invalid=Set<String>()
 private static let isoFractional:ISO8601DateFormatter={let f=ISO8601DateFormatter();f.formatOptions=[.withInternetDateTime,.withFractionalSeconds];return f}()
 private static let isoPlain=ISO8601DateFormatter()
 private static let rfc:DateFormatter={let f=DateFormatter();f.locale=Locale(identifier:"en_US_POSIX");f.timeZone=TimeZone(secondsFromGMT:0);return f}()
 static func parse(_ s:String)->Date? {
  guard !s.isEmpty else{return nil}
  lock.lock();defer{lock.unlock()}
  if let d=cache[s]{return d};if invalid.contains(s){return nil}
  var parsed=isoFractional.date(from:s) ?? isoPlain.date(from:s)
  if parsed==nil {for format in ["EEE, dd MMM yyyy HH:mm:ss zzz","EEE, d MMM yyyy HH:mm:ss zzz"]{rfc.dateFormat=format;if let d=rfc.date(from:s){parsed=d;break}}}
  if cache.count+invalid.count>20000{cache.removeAll();invalid.removeAll()}
  if let d=parsed{cache[s]=d}else{invalid.insert(s)}
  return parsed
 }
 static func display(_ d:Date?)->String {
  guard let d else{return "وقت غير معروف"};let f=DateFormatter();f.locale=Locale(identifier:"ar_JO");f.timeZone=zone;f.dateFormat="dd MMM، HH:mm";return f.string(from:d)
 }
 static func retained(_ r:Article,now:Date=Date())->Bool {
  guard let d=r.date ?? r.discovered.flatMap(parse) else{return false};return d>=now.addingTimeInterval(-96*3600)
 }
}
enum Period:String,CaseIterable,Identifiable {
 case all="الكل",today="اليوم",yesterday="أمس",three="آخر 3 ساعات",nine="آخر 9 ساعات"
 var id:String{rawValue}
 func contains(_ r:Article,now:Date=Date())->Bool {
  if self == .all{return true};guard let d=r.date,d<=now else{return false}
  var cal=Calendar(identifier:.gregorian);cal.timeZone=Dates.zone;let start=cal.startOfDay(for:now)
  switch self {
   case .all:return true
   case .today:return d>=start
   case .yesterday:return d>=cal.date(byAdding:.day,value:-1,to:start)! && d<start
   case .three:return d>=now.addingTimeInterval(-3*3600)
   case .nine:return d>=now.addingTimeInterval(-9*3600)
  }
 }
}
struct Filters:Equatable {
 var period:Period = .all;var language="الكل";var impact="كل الاتجاهات";var relevance="مباشر وغير مباشر";var keyword="كل الكلمات";var query="";var publisher="الكل";var platform="الكل";var region="الكل"
 static let keywords=["كل الكلمات","وزارة السياحة والآثار الأردنية","عماد حجازين","وزير السياحة والآثار الدكتور عماد حجازين"]
 func matches(_ r:Article,now:Date=Date())->Bool {
  guard Dates.retained(r,now:now),period.contains(r,now:now) else{return false}
  if language != "الكل" && r.language != language{return false}
  if impact != "كل الاتجاهات" && impact != r.sentiment{return false}
  if relevance == "مباشر وغير مباشر" {if !["مباشر","غير مباشر"].contains(r.relevance){return false}}
  else if relevance != r.relevance{return false}
  if keyword != "كل الكلمات" && !(r._matched_keywords ?? []).contains(keyword) && !TextRules.norm(r.evidence).contains(TextRules.norm(keyword)){return false}
  if platform != "الكل" && r.platform != platform{return false}
  if publisher != "الكل" && publisher != r.source{return false}
  if region != "الكل" && region != r.publisherRegion{return false}
  return query.isEmpty || TextRules.norm(r.evidence+" "+r.source+" "+(r._places ?? []).joined(separator:" ")).contains(TextRules.norm(query))
 }
}
enum TextRules {
 static func norm(_ s:String)->String {
  s.lowercased().replacingOccurrences(of:"[\\u064B-\\u065F\\u0670ـ]",with:"",options:.regularExpression).replacingOccurrences(of:"[أإآ]",with:"ا",options:.regularExpression).replacingOccurrences(of:"ى",with:"ي").replacingOccurrences(of:"\\s+",with:" ",options:.regularExpression).trimmingCharacters(in:.whitespacesAndNewlines)
 }
 static func has(_ s:String,_ words:[String])->Bool { words.contains { w in s.range(of:"(?<![\\p{L}\\p{N}])"+NSRegularExpression.escapedPattern(for:norm(w))+"(?![\\p{L}\\p{N}])",options:.regularExpression) != nil } }
 static let tourism=["السياحة","السياحي","السياحية","السياح","سياح","سياحة","سائح","فندق","فنادق","منتجع","tourism","tourist","tourists","travel","hotel","hotels","resort"]
 static let indirect=["آثار","الأثرية","تراث","قلعة","متحف","محمية","طيران","مطار","تأشيرة","تحذيرات السفر","heritage","archaeology","castle","museum","airport","flights","visa","travel advisory"]
 static let names=["عماد حجازين","عماد الحجازين","Imad Hijazin","Emad Hijazin","Imad Hijazeen","Emad Hijazeen","Imad Hijazine","Emad Hijazine"]
 static func analyze(_ original:Article,places:[Place])->Article {
  var r=original;let s=norm(r.evidence)
  let country=has(s,["الأردن","الأردنية","الأردني","Jordanian"]) || s.range(of:"\\b(in|to|from|of|visit) jordan\\b|\\bjordan (tourism|travel)\\b|\\bjordan[’']s\\b",options:.regularExpression) != nil
  let known=has(s,["عمان","عمّان","إربد","اربد","الزرقاء","السلط","الفحيص","الطفيلة","معان","الكرك","المفرق","وادي موسى","Amman","Irbid","Zarqa","Tafilah","Mafraq","Fuheis","Wadi Musa","العقبة","البترا","البتراء","وادي رم","جرش","عجلون","مادبا","Aqaba","Petra","Wadi Rum","Jerash","Ajloun","Madaba","قلعة الكرك","Karak Castle"])
  let official=has(s,names+["وزارة السياحة والآثار الأردنية","هيئة تنشيط السياحة الأردنية","دائرة الآثار العامة الأردنية","أردننا جنة","Jordan Tourism Board","Jordan Ministry of Tourism"])
  let found=places.filter { has(s,[$0.ar,$0.en].filter { $0.count>=3 }) }.prefix(12).map(\.ar)
  r._places=Array(found)
  if has(s,["Michael Jordan","Air Jordan","Jordan Brown"]) && !country && !known && !official {r._relevance="مستبعد"}
  else if official {r._relevance="مباشر"}
  else if country || known {r._relevance=has(s,tourism) ? "مباشر" : has(s,indirect) ? "غير مباشر" : "للمراجعة"}
  else {r._relevance=found.isEmpty ? "مستبعد" : "للمراجعة"}
  r._relevance_reason="تقدير من النص المتاح؛ ذكر مدينة وحده لا يؤكد الصلة بالسياحة الأردنية."
  let neg=has(s,["انتقاد","شكاوى","إغلاق","الغاء","تراجع","انخفاض","مقتل","إصابة","هجوم","criticism","decline","cancellation","attack","closure"])
  let pos=has(s,["ارتفاع","نمو","افتتاح","ترميم","زيادة","تطوير","growth","recovery","award","restoration","new flights"])
  let uncertain=has(s,["ينفي","تنفي","نفي","مزاعم","غير صحيح","denies","not true","rumours"])
  let label=uncertain || (neg && pos) || !["مباشر","غير مباشر"].contains(r.relevance) ? "يحتاج مراجعة" : neg ? "سلبي" : pos ? "إيجابي" : "محايد"
  r._impact=[label,"تصنيف تقديري حسب النص المتاح؛ راجع المصدر قبل الاعتماد."]
  var keywords:[String]=[]
  if has(s,["وزارة السياحة والآثار الأردنية","وزارة السياحة والآثار","Jordan Ministry of Tourism","Ministry of Tourism and Antiquities"]) {keywords.append(Filters.keywords[1])}
  if has(s,names){keywords.append(Filters.keywords[2]);if has(s,["وزير السياحة","tourism minister","minister of tourism"]){keywords.append(Filters.keywords[3])}}
  r._matched_keywords=keywords;r.text_scope=r.body?.isEmpty == false ? "imported text" : "headline and summary only";return r
 }
}

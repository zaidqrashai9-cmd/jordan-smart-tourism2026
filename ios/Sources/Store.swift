import Foundation
import SwiftUI

@MainActor final class MonitorStore:ObservableObject {
 @Published var feed=Feed.empty
 @Published var manualSocial:[Article]=[]
 @Published var busy=false
 @Published var notice=""
 @Published var lastSync:Date?
 let directory=PlaceDirectory.bundled()
 let feedURL=URL(string:"https://raw.githubusercontent.com/zaidqrashai9-cmd/jordan-smart-tourism2026/main/data/news.json")!
 private let folder:URL
 private var queryCursor=0
 init(testing:Bool=false){
  folder=FileManager.default.urls(for:.documentDirectory,in:.userDomainMask)[0]
  if testing {notice="وضع فحص الواجهة — بيانات الاختبار معزولة";return}
  let cache=folder.appendingPathComponent("news-cache.json")
  if let d=try? Data(contentsOf:cache),let f=try? JSONDecoder().decode(Feed.self,from:d){feed=f}
  else if let u=Bundle.main.url(forResource:"news",withExtension:"json"),let d=try? Data(contentsOf:u),let f=try? JSONDecoder().decode(Feed.self,from:d){feed=f;notice="أرشيف مرفق من جمع فعلي؛ حدّثه للحصول على أحدث النتائج."}
  if let d=try? Data(contentsOf:folder.appendingPathComponent("social-private.json")),let rows=try? JSONDecoder().decode([Article].self,from:d){manualSocial=rows}
  queryCursor=UserDefaults.standard.integer(forKey:"query-cursor");prune()
 }
 var items:[Article]{feed.items.filter{Dates.retained($0)}.sorted{($0.date ?? .distantPast)>($1.date ?? .distantPast)}}
 var social:[Article]{((feed.social_items ?? [])+manualSocial).filter{Dates.retained($0)}.sorted{($0.date ?? Dates.parse($0.discovered ?? "") ?? .distantPast)>($1.date ?? Dates.parse($1.discovered ?? "") ?? .distantPast)}}
 var latest:Date?{items.filter{["مباشر","غير مباشر"].contains($0.relevance)}.compactMap(\.date).max()}
 var today:Int{items.filter{Period.today.contains($0) && ["مباشر","غير مباشر"].contains($0.relevance)}.count}
 func prune(){feed.items.removeAll{!Dates.retained($0)};feed.social_items?.removeAll{!Dates.retained($0)};manualSocial.removeAll{!Dates.retained($0)};save()}
 func save(){if let data=try? JSONEncoder().encode(feed){try? data.write(to:folder.appendingPathComponent("news-cache.json"),options:.atomic)};if let data=try? JSONEncoder().encode(manualSocial){try? data.write(to:folder.appendingPathComponent("social-private.json"),options:.atomic)}}
 func sync()async{
  guard !busy else{return};busy=true;defer{busy=false}
  do {var req=URLRequest(url:feedURL);req.cachePolicy = .reloadIgnoringLocalCacheData;req.timeoutInterval=35
   let (data,response)=try await URLSession.shared.data(for:req)
   guard let http=response as? HTTPURLResponse,http.statusCode==200,data.count<20_000_000 else{throw URLError(.badServerResponse)}
   var incoming=try JSONDecoder().decode(Feed.self,from:data)
   // Keep locally discovered articles if they have not reached the shared feed yet.
   var map=Dictionary(incoming.items.map{($0.url,$0)},uniquingKeysWith:{a,_ in a})
   for r in feed.items where map[r.url]==nil {map[r.url]=r};incoming.items=Array(map.values)
   feed=incoming;lastSync=Date();prune();notice="تمت مزامنة الأرشيف. أحدث خبر: \(Dates.display(latest))."
  }catch{notice="تعذّر الاتصال بالأرشيف المشترك. المعروض هو المحفوظ على الهاتف. يمكنك إعادة المزامنة أو البحث المباشر.\n\(error.localizedDescription)"}
 }
 func searchNow()async{
  guard !busy else{return};busy=true;notice="جارٍ البحث من الهاتف؛ الأرشيف المحفوظ متاح أثناء الجلب…";defer{busy=false}
  let results=await RSSCollector.search(cursor:queryCursor);queryCursor+=12;UserDefaults.standard.set(queryCursor,forKey:"query-cursor")
  var map=Dictionary(feed.items.map{($0.url,$0)},uniquingKeysWith:{a,_ in a});var added=0
  for r in results.0 {if map[r.url]==nil {var row=TextRules.analyze(r,places:directory?.items ?? []);row.discovered=ISO8601DateFormatter().string(from:Date());map[row.url]=row;added+=1}}
  feed.items=Array(map.values);feed.sources=results.1;feed.updated=ISO8601DateFormatter().string(from:Date());feed.new_items=added
  if results.1.contains(where:{$0.error==nil}) {feed.last_success=feed.updated};prune()
  let failed=results.1.filter{$0.error != nil}.count
  notice=failed==results.1.count ? "تعذرت كل مصادر هذه المحاولة؛ الأرشيف السابق محفوظ." : "اكتمل البحث: \(added) مادة جديدة، و\(failed) استعلامات متعذرة. التصنيف من العنوان والملخص ما لم يتوفر نص محفوظ."
 }
 func addSocial(platform:String,account:String,text:String,url:String,published:Date?){
  guard let link=URL(string:url),link.scheme=="https",!text.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty else{notice="أدخل نصًا ورابط HTTPS صالحًا.";return}
  let date=published.map{ISO8601DateFormatter().string(from:$0)} ?? ""
  var row=Article(id:UUID().uuidString,title:String(text.prefix(180)),source:account.isEmpty ? platform : account,url:url,published:date,discovered:ISO8601DateFormatter().string(from:Date()),summary:text,platform:platform,account:account,manual:true)
  row=TextRules.analyze(row,places:directory?.items ?? []);manualSocial.append(row);prune();notice="تمت إضافة المنشور محليًا. لم يُنشر على خادم أو يُرسل لأي شخص."
 }
 func importArchive(_ url:URL)throws{
  let allowed=url.startAccessingSecurityScopedResource();defer{if allowed{url.stopAccessingSecurityScopedResource()}}
  let data=try Data(contentsOf:url);guard data.count<20_000_000 else{throw URLError(.dataLengthExceedsMaximum)}
  let archive=try JSONDecoder().decode(Feed.self,from:data);var map=Dictionary(feed.items.map{($0.url,$0)},uniquingKeysWith:{a,_ in a})
  for var row in archive.items where row.link != nil {if row.discovered==nil{row.discovered=ISO8601DateFormatter().string(from:Date())};if row._relevance==nil{row=TextRules.analyze(row,places:directory?.items ?? [])};map[row.url]=row}
  feed.items=Array(map.values);prune();notice="تم استيراد الأرشيف والنصوص المتاحة إلى الهاتف، مع تطبيق الاحتفاظ لأربعة أيام."
 }
 func csv(_ rows:[Article])->String{
  func cell(_ s:String)->String{var value=s;if let first=s.first,"=+-@".contains(first){value="'"+s};return "\""+value.replacingOccurrences(of:"\"",with:"\"\"")+"\""}
  let header=["العنوان","المصدر","وقت النشر — عمّان","الرابط","الصلة","الاتجاه التقديري","اللغة"]
  return "\u{FEFF}"+([header]+rows.map{[$0.title,$0.source,Dates.display($0.date),$0.link?.absoluteString ?? $0.url,$0.relevance,$0.sentiment,$0.language]}).map{$0.map(cell).joined(separator:",")}.joined(separator:"\r\n")
 }
}
struct QueryPlan:Codable {var priority:[String];var queries:[String]}
enum RSSCollector {
 static func search(cursor:Int)async->([Article],[SourceStatus]){
  guard let u=Bundle.main.url(forResource:"queries",withExtension:"json"),let d=try? Data(contentsOf:u),let plan=try? JSONDecoder().decode(QueryPlan.self,from:d),!plan.queries.isEmpty else{return ([],[SourceStatus(query:"قائمة الاستعلامات",count:0,error:"قائمة البحث غير متاحة")])}
  let rotating=(0..<12).map{plan.queries[(cursor+$0)%plan.queries.count]};let jobs=Array(Set(plan.priority+rotating)).sorted();var rows:[Article]=[];var statuses:[SourceStatus]=[]
  // Three simultaneous requests keep the phone responsive and avoid request bursts.
  for offset in stride(from:0,to:jobs.count,by:3){
   let batch=Array(jobs[offset..<min(offset+3,jobs.count)])
   let results=await withTaskGroup(of:([Article],SourceStatus).self,returning:[([Article],SourceStatus)].self){group in
    for q in batch{group.addTask{
     do{let en=q.unicodeScalars.allSatisfy(\.isASCII);var c=URLComponents(string:"https://news.google.com/rss/search")!;c.queryItems=[URLQueryItem(name:"q",value:q+" when:4d"),URLQueryItem(name:"hl",value:en ? "en":"ar"),URLQueryItem(name:"gl",value:en ? "US":"JO"),URLQueryItem(name:"ceid",value:en ? "US:en":"JO:ar")]
      var req=URLRequest(url:c.url!);req.timeoutInterval=12;req.setValue("JordanTourismMonitor/2.0",forHTTPHeaderField:"User-Agent")
      let (bytes,response)=try await URLSession.shared.data(for:req);guard (response as? HTTPURLResponse)?.statusCode==200 else{throw URLError(.badServerResponse)}
      let parser=FeedParser();let xml=XMLParser(data:bytes);xml.shouldResolveExternalEntities=false;xml.delegate=parser;guard xml.parse() else{throw URLError(.cannotParseResponse)}
      return (parser.rows,SourceStatus(query:q,count:parser.rows.count,error:nil,provider:"Google News — بحث الهاتف"))
     }catch{return ([],SourceStatus(query:q,count:0,error:error.localizedDescription,provider:"Google News — بحث الهاتف"))}
    }}
    var out:[([Article],SourceStatus)]=[];for await r in group{out.append(r)};return out
   }
   for r in results{rows+=r.0;statuses.append(r.1)}
  }
  return (rows,statuses)
 }
}
final class FeedParser:NSObject,XMLParserDelegate {
 var rows:[Article]=[];private var fields:[String:String]=[:];private var current="";private var inside=false
 func parser(_ parser:XMLParser,didStartElement name:String,namespaceURI:String?,qualifiedName:String?,attributes:[String:String]){if name=="item"{inside=true;fields=[:]}else if inside{current=name}}
 func parser(_ parser:XMLParser,foundCharacters string:String){if inside{fields[current,default:""]+=string}}
 func parser(_ parser:XMLParser,foundCDATA CDATABlock:Data){if let string=String(data:CDATABlock,encoding:.utf8),inside{fields[current,default:""]+=string}}
 func parser(_ parser:XMLParser,didEndElement name:String,namespaceURI:String?,qualifiedName:String?){
  if name=="item" {defer{inside=false;current=""};guard let title=fields["title"],let url=fields["link"],URL(string:url)?.scheme=="https" else{return};let summary=(fields["description"] ?? "").replacingOccurrences(of:"<[^>]+>",with:" ",options:.regularExpression).replacingOccurrences(of:"&nbsp;",with:" ").replacingOccurrences(of:"&amp;",with:"&");rows.append(Article(id:url,title:title,source:fields["source"] ?? "مصدر غير محدد",url:url,published:fields["pubDate"] ?? "",discovered:ISO8601DateFormatter().string(from:Date()),summary:summary))
  };current=""
 }
}

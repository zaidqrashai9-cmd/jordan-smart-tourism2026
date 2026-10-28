import SwiftUI
import UniformTypeIdentifiers
import UIKit

extension Color {
 static let forest=Color(red:0.07,green:0.24,blue:0.19)
 static let paper=Color(red:0.95,green:0.96,blue:0.94)
 static let sand=Color(red:0.83,green:0.70,blue:0.47)
}
@main @MainActor struct MediaMonitorApp:App {
 @StateObject private var store=MonitorStore(testing:ProcessInfo.processInfo.arguments.contains("-ui-testing"))
 @Environment(\.scenePhase) private var phase
 private let testing=ProcessInfo.processInfo.arguments.contains("-ui-testing")
 var body:some Scene {
  WindowGroup {
   TabView {
    NewsScreen(social:false).tabItem{Label("الأخبار",systemImage:"newspaper")}.accessibilityIdentifier("news-tab")
    NewsScreen(social:true).tabItem{Label("السوشال ميديا",systemImage:"bubble.left.and.bubble.right")}.accessibilityIdentifier("social-tab")
    StatusScreen().tabItem{Label("المصادر",systemImage:"checklist")}.accessibilityIdentifier("sources-tab")
   }.tint(.forest).environmentObject(store).environment(\.layoutDirection,.rightToLeft)
    .task{if !testing{await store.sync()}}
    .onChange(of:phase){_,value in if value == .active && !testing {store.prune();Task{await store.sync()}}}
    .onReceive(Timer.publish(every:60,on:.main,in:.common).autoconnect()){_ in if !testing{store.prune()}}
  }
 }
}
struct NewsScreen:View {
 @EnvironmentObject var store:MonitorStore
 let social:Bool
 @State private var filters=Filters()
 @State private var showFilters=false
 @State private var showManual=false
 private var rows:[Article]{(social ? store.social:store.items).filter{filters.matches($0)}}
 var body:some View {
  NavigationStack {
   ScrollView {
    VStack(alignment:.leading,spacing:18){
     if !social {hero}
     if social {socialConnections}
     periodBar
     HStack {Text("\(rows.count) مادة مطابقة").font(.headline);Spacer();Button("مسح الفلاتر"){filters=Filters()}.font(.caption)}
     if !store.notice.isEmpty {Text(store.notice).font(.caption).foregroundStyle(.secondary).padding(12).frame(maxWidth:.infinity,alignment:.leading).background(Color.sand.opacity(0.15),in:RoundedRectangle(cornerRadius:12)).accessibilityIdentifier("status-message")}
     if rows.isEmpty {ContentUnavailableView("لا توجد نتائج مطابقة",systemImage:social ? "bubble.left.and.bubble.right":"newspaper",description:Text(social ? "المنصات غير المتصلة لا تُرصد تلقائيًا. أضف رابطًا عامًا يدويًا أو راجع فلاتر الصلة والوقت.":"جرّب فترة أوسع أو تصنيف «للمراجعة». عدم وجود نتائج قد يعني عدم وجود أخبار محفوظة أو تعذر مصدر."))}
     LazyVStack(spacing:14){ForEach(rows.prefix(500)){r in NavigationLink {ArticleScreen(article:r)} label:{ArticleCard(article:r)}.buttonStyle(.plain)}}
     if rows.count>500 {Text("يُعرض أول 500 مادة. ضيّق البحث لعرض البقية.").font(.caption).foregroundStyle(.secondary)}
     Text("الأوقات بتوقيت عمّان · الاحتفاظ 4 أيام · التصنيف تقديري").font(.caption2).foregroundStyle(.secondary)
    }.padding()
   }.background(Color.paper).navigationTitle(social ? "السوشال ميديا":"رصد وحدة الاعلام").navigationBarTitleDisplayMode(.inline)
    .searchable(text:$filters.query,prompt:"ابحث في العنوان والنص المتاح")
    .toolbar {
     ToolbarItem(placement:.topBarTrailing){Button{showFilters=true}label:{Image(systemName:"line.3.horizontal.decrease.circle")}.accessibilityLabel("الفلاتر").accessibilityIdentifier("filters-button")}
     if social {ToolbarItem(placement:.topBarLeading){Button{showManual=true}label:{Image(systemName:"plus")}.accessibilityLabel("إضافة منشور يدويًا")}}
    }
    .safeAreaInset(edge:.bottom){
     HStack(spacing:10){
      Button{Task{await store.sync()}}label:{Label("مزامنة الأرشيف",systemImage:"arrow.clockwise").frame(maxWidth:.infinity)}.buttonStyle(.bordered)
      if !social {Button{Task{await store.searchNow()}}label:{HStack{if store.busy{ProgressView().tint(.white)};Text(store.busy ? "جارٍ البحث…":"بحث من الهاتف")}.frame(maxWidth:.infinity)}.buttonStyle(.borderedProminent)}
     }.font(.callout).disabled(store.busy).padding(12).background(.regularMaterial)
    }
    .refreshable{await store.sync()}
    .sheet(isPresented:$showFilters){FilterSheet(filters:$filters,sources:Array(Set((social ? store.social:store.items).map(\.source))).sorted(),social:social)}
    .sheet(isPresented:$showManual){ManualSocialSheet()}
  }
 }
 private var hero:some View {
  VStack(alignment:.leading,spacing:12){
   HStack{Image(systemName:"building.columns").foregroundStyle(Color.sand);Text("رصد السياحة الأردنية").font(.title2.bold());Spacer()}
   Text("أخبار الأردن السياحية… مباشرة وغير مباشرة").font(.subheadline).foregroundStyle(.white.opacity(0.8))
   HStack{Label("\(store.today) اليوم",systemImage:"calendar");Spacer();Text("أحدث خبر: \(Dates.display(store.latest))").font(.caption)}
   if let updated=Dates.parse(store.feed.updated ?? ""){Text("آخر محاولة جمع: \(Dates.display(updated))").font(.caption2).foregroundStyle(.white.opacity(0.75))}
  }.foregroundStyle(.white).padding(20).frame(maxWidth:.infinity,alignment:.leading).background(Color.forest,in:RoundedRectangle(cornerRadius:22)).accessibilityIdentifier("news-hero")
 }
 private var periodBar:some View {
  ScrollView(.horizontal,showsIndicators:false){HStack{ForEach(Period.allCases){p in Button{filters.period=p}label:{Text(p.rawValue).font(.subheadline).padding(.horizontal,16).padding(.vertical,10).background(filters.period==p ? Color.forest:Color.white,in:Capsule()).foregroundStyle(filters.period==p ? Color.white:Color.forest)}.accessibilityIdentifier("period-\(p.id)")}}}
 }
 private var socialConnections:some View {
  VStack(alignment:.leading,spacing:12){
   Text("اتصال المنصات").font(.headline)
   let states=store.feed.social_sources ?? ["Facebook","Instagram","X"].map{SocialStatus(platform:$0,connected:false,count:0,message:"غير متصل — يلزم وصول API مصرح به. الإضافة اليدوية متاحة.")}
   ForEach(states){s in HStack(alignment:.top){Image(systemName:s.connected ? "checkmark.circle.fill":"minus.circle").foregroundStyle(s.connected ? .green:.secondary);VStack(alignment:.leading,spacing:4){Text(s.platform).font(.subheadline.bold());Text(s.message).font(.caption).foregroundStyle(.secondary)};Spacer()}}
   Text("المنشورات اليدوية تُحفظ على هاتفك فقط. لا نعطي انطباعًا برصد شامل لمنصة غير متصلة.").font(.caption).foregroundStyle(.secondary)
  }.padding().background(.white,in:RoundedRectangle(cornerRadius:18))
 }
}
struct ArticleCard:View {
 let article:Article
 var body:some View {
  VStack(alignment:.leading,spacing:12){
   HStack{Text(article.source).font(.caption.bold());Text(article.language).font(.caption2);Spacer();Text(Dates.display(article.date)).font(.caption2).foregroundStyle(.secondary)}
   Text(article.title).font(.headline).multilineTextAlignment(.leading).foregroundStyle(Color.forest).frame(maxWidth:.infinity,alignment:.leading)
   if let summary=article.summary,!summary.isEmpty{Text(summary).font(.subheadline).foregroundStyle(.secondary).lineLimit(3)}
   HStack{badge(article.relevance,color:.forest);badge(article.sentiment,color:article.sentiment=="سلبي" ? .red:article.sentiment=="إيجابي" ? .green:.secondary);if article.manual==true{badge("إضافة يدوية",color:.orange)}}
  }.padding(18).background(Color.white,in:RoundedRectangle(cornerRadius:18)).overlay(RoundedRectangle(cornerRadius:18).stroke(Color.forest.opacity(0.09)))
 }
 private func badge(_ text:String,color:Color)->some View {Text(text).font(.caption2).padding(.horizontal,9).padding(.vertical,5).foregroundStyle(color).background(color.opacity(0.08),in:Capsule())}
}
struct ArticleScreen:View {
 let article:Article
 var body:some View {
  ScrollView{VStack(alignment:.leading,spacing:20){
   Text(article.title).font(.title2.bold()).textSelection(.enabled)
   Text("\(article.source) · \(Dates.display(article.date))").font(.subheadline).foregroundStyle(.secondary)
   LabeledContent("الصلة",value:article.relevance);LabeledContent("الاتجاه التقديري",value:article.sentiment)
   Text(article._relevance_reason ?? "التصنيف يحتاج مراجعة النص المتاح.").font(.caption).foregroundStyle(.secondary)
   if let why=article._impact?.dropFirst().first{Text(why).font(.caption).foregroundStyle(.secondary)}
   if let places=article._places,!places.isEmpty{Text("المواقع المطابقة: "+places.joined(separator:"، ")).font(.caption)}
   if let body=article.body,!body.isEmpty {Text(article.text_scope=="body analyzed; excerpt displayed" ? "مقتطف من النص الذي جرى تحليله":"النص المحفوظ").font(.headline);Text(body).textSelection(.enabled)}
   else if let summary=article.summary{Text("العنوان والملخص المتاحان").font(.headline);Text(summary).textSelection(.enabled)}
   Text("التصنيف تقديري من المحتوى المتاح. افتح المصدر لقراءة الخبر الأصلي كاملًا.").font(.caption).foregroundStyle(.secondary)
   if let link=article.link{Link(destination:link){Label("فتح المصدر الأصلي",systemImage:"arrow.up.right.square").frame(maxWidth:.infinity)}.buttonStyle(.borderedProminent)}
   ShareLink(item:article.shareText){Label("مشاركة — واتساب أو تطبيق آخر",systemImage:"square.and.arrow.up")}.buttonStyle(.bordered)
   Button{UIPasteboard.general.string=article.shareText}label:{Label("نسخ العنوان والمصدر والرابط",systemImage:"doc.on.doc")}.buttonStyle(.bordered)
  }.frame(maxWidth:.infinity,alignment:.leading).padding()}.navigationTitle("تفاصيل المادة").navigationBarTitleDisplayMode(.inline)
 }
}
struct FilterSheet:View {
 @Binding var filters:Filters;let sources:[String];let social:Bool
 @Environment(\.dismiss) var dismiss
 var body:some View {
  NavigationStack{Form {
   Picker("الفترة",selection:$filters.period){ForEach(Period.allCases){Text($0.rawValue).tag($0)}}
   Picker("اللغة",selection:$filters.language){ForEach(["الكل","AR","EN"],id:\.self){Text($0).tag($0)}}
   Picker("اتجاه الخبر",selection:$filters.impact){ForEach(["كل الاتجاهات","إيجابي","سلبي","محايد","يحتاج مراجعة"],id:\.self){Text($0).tag($0)}}
   Picker("الصلة بالسياحة",selection:$filters.relevance){ForEach(["مباشر وغير مباشر","مباشر","غير مباشر","للمراجعة","مستبعد"],id:\.self){Text($0).tag($0)}}
   Picker("الكلمة المفتاحية",selection:$filters.keyword){ForEach(Filters.keywords,id:\.self){Text($0).tag($0)}}
   Picker("المصدر",selection:$filters.publisher){ForEach(["الكل"]+sources,id:\.self){Text($0).tag($0)}}
   if social {Picker("المنصة",selection:$filters.platform){ForEach(["الكل","Facebook","Instagram","X"],id:\.self){Text($0).tag($0)}}}
   Section{Text("المدن والبلدات جزء من البحث، وليست خيارات إضافية في قائمة الكلمات. فلاتر الوقت تعتمد وقت النشر الأصلي بتوقيت عمّان.").font(.caption).foregroundStyle(.secondary);Button("إعادة ضبط الفلاتر"){filters=Filters()}}
  }.navigationTitle("الفلاتر").toolbar{ToolbarItem(placement:.confirmationAction){Button("تم"){dismiss()}.accessibilityIdentifier("filters-done")}}}
 }
}
struct ManualSocialSheet:View {
 @EnvironmentObject var store:MonitorStore
 @Environment(\.dismiss) var dismiss
 @State var platform="Facebook";@State var account="";@State var text="";@State var url="";@State var knownDate=false;@State var date=Date()
 private var valid:Bool{URL(string:url)?.scheme=="https" && !text.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty}
 var body:some View{NavigationStack{Form{
  Section("منشور عام — إضافة يدوية"){
   Picker("المنصة",selection:$platform){ForEach(["Facebook","Instagram","X"],id:\.self){Text($0)}}
   TextField("اسم الحساب أو الصفحة",text:$account)
   TextField("رابط HTTPS للمنشور",text:$url).textInputAutocapitalization(.never).keyboardType(.URL).environment(\.layoutDirection,.leftToRight)
   TextEditor(text:$text).frame(minHeight:160).accessibilityLabel("نص المنشور")
  }
  Toggle("أعرف وقت النشر الأصلي",isOn:$knownDate)
  if knownDate{DatePicker("وقت النشر",selection:$date,in:...Date())}
  Text("لا نقرأ حسابك ولا نطلب كلمة مروره. يُحفظ النص على هذا الهاتف، ويُحذف من العرض بعد أربعة أيام. عند غياب وقت النشر يُستخدم وقت الإضافة للاحتفاظ فقط، ويظهر المنشور في «الكل».").font(.caption).foregroundStyle(.secondary)
 }.navigationTitle("إضافة منشور").toolbar{ToolbarItem(placement:.cancellationAction){Button("إلغاء"){dismiss()}};ToolbarItem(placement:.confirmationAction){Button("حفظ"){store.addSocial(platform:platform,account:account,text:text,url:url,published:knownDate ? date:nil);dismiss()}.disabled(!valid)}}}}
}
struct StatusScreen:View {
 @EnvironmentObject var store:MonitorStore
 @State private var importer=false;@State private var exporter=false;@State private var exportData=Data();@State private var kind=UTType.json;@State private var filename="jordan-tourism"
 var body:some View {NavigationStack {List {
  Section("حالة التحديث"){
   LabeledContent("آخر محاولة جمع",value:Dates.display(Dates.parse(store.feed.updated ?? "")))
   LabeledContent("آخر استجابة ناجحة",value:Dates.display(Dates.parse(store.feed.last_success ?? "")))
   LabeledContent("أحدث خبر ذي صلة",value:Dates.display(store.latest))
   LabeledContent("آخر مزامنة على الهاتف",value:Dates.display(store.lastSync))
   LabeledContent("مواد جديدة في آخر محاولة",value:String(store.feed.new_items ?? 0))
   Text("الخادم يستهدف الجمع كل ساعة عبر GitHub Actions؛ قد يتأخر التنفيذ أو يتوقف وفق قيود المزود. زر «بحث من الهاتف» يجلب دفعة إضافية مباشرة أثناء الفتح. لا ندّعي رصد كل الإنترنت.").font(.caption).foregroundStyle(.secondary)
  }
  Section("دليل المواقع"){
   NavigationLink{PlacesScreen()}label:{Label("المدن والبلدات والتجمعات — عربي / English",systemImage:"map")}.accessibilityIdentifier("places-link")
   Text("\(store.directory?.locality_count ?? 0) تجمعًا من المحافظات الـ12 — مصدر رسمي لعام 2025. بعض الصفوف تجمع عدة أحياء؛ نحافظ على تصنيف المصدر ولا نسمي كل صف مدينة.").font(.caption).foregroundStyle(.secondary)
   if let u=URL(string:store.directory?.source ?? ""){Link("مصدر دائرة الإحصاءات العامة",destination:u)}
  }
  Section("الأرشيف والمشاركة"){
   Button("استيراد أرشيف JSON من الكمبيوتر"){importer=true}
   Button("تصدير أرشيف الأخبار JSON"){exportData=(try? JSONEncoder().encode(store.feed)) ?? Data();kind = .json;filename="jordan-tourism-archive";exporter=true}
   Button("تصدير الأخبار المرتبطة CSV"){exportData=Data(store.csv(store.items.filter{["مباشر","غير مباشر"].contains($0.relevance)}).utf8);kind = .commaSeparatedText;filename="jordan-tourism-news";exporter=true}
   Text("التصدير لا يرسل شيئًا تلقائيًا لأي شخص. المنشورات اليدوية لا تدخل الأرشيف المشترك.").font(.caption).foregroundStyle(.secondary)
  }
  Section("نتائج الاتصال بالمصادر"){
   if let sources=store.feed.sources,!sources.isEmpty {ForEach(sources){s in VStack(alignment:.leading,spacing:5){Text(s.query).font(.caption);Text(s.error.map{"تعذر الجلب: "+$0} ?? "\(s.count) نتيجة من \(s.provider ?? "المصدر")").font(.caption2).foregroundStyle(s.error==nil ? Color.secondary:Color.red)}}}
   else{Text("لم تُحمّل حالة المصادر بعد.").foregroundStyle(.secondary)}
  }
  Section("الخصوصية وحدود النص"){
   Text("لا يحتوي التطبيق بيانات دخول OpenAI أو GitHub أو Apple. الأخبار العامة تُجمع في أرشيف مشترك، والاستيراد والإضافة اليدوية محليان. فحص الكلمات قد يستخدم نصًا مستخرجًا على الخادم؛ يُعرض مقتطف فقط، ويفتح النص الكامل لدى ناشره. التصنيف من العنوان والملخص عند تعذر الاستخراج. انتهاء المحتوى يُطبق عند فتح الأرشيف ودوريًا أثناء تشغيل التطبيق.").font(.caption)
   Text("رصد وحدة الاعلام · iPhone 2.0 · واجهة SwiftUI أصلية").font(.caption2).foregroundStyle(.secondary)
  }
 }.navigationTitle("المصادر والإعدادات")
  .fileImporter(isPresented:$importer,allowedContentTypes:[.json]){result in do{try store.importArchive(result.get())}catch{store.notice="تعذر الاستيراد: "+error.localizedDescription}}
  .fileExporter(isPresented:$exporter,document:ExportDocument(data:exportData),contentType:kind,defaultFilename:filename){result in if case .failure(let error)=result{store.notice="تعذر التصدير: "+error.localizedDescription}}
 }}
}
struct PlacesScreen:View {
 @EnvironmentObject var store:MonitorStore
 @State private var query=""
 private var rows:[Place]{(store.directory?.items ?? []).filter{query.isEmpty || TextRules.norm([$0.ar,$0.en,$0.governorate,$0.district].joined(separator:" ")).contains(TextRules.norm(query))}}
 var body:some View {List{
  Section{Text("\(rows.count) سجل مطابق. الأسماء الإنجليزية كما وردت في المصدر الرسمي، مع المحافظة واللواء لتفادي التباس الأسماء.").font(.caption).foregroundStyle(.secondary)}
  ForEach(rows){p in VStack(alignment:.leading,spacing:5){HStack{Text(p.ar).font(.headline);Spacer();Text(p.type=="governorate" ? "محافظة":"تجمع سكاني").font(.caption2).foregroundStyle(.secondary)};Text(p.en).font(.subheadline).environment(\.layoutDirection,.leftToRight);Text([p.governorate,p.district].filter{!$0.isEmpty}.joined(separator:" · ")).font(.caption).foregroundStyle(.secondary)}}
 }.navigationTitle("دليل الأردن").searchable(text:$query,prompt:"مدينة، بلدة، محافظة — AR / EN")}
}
struct ExportDocument:FileDocument {
 static var readableContentTypes:[UTType]{[.json,.commaSeparatedText,.plainText]}
 var data:Data
 init(data:Data){self.data=data}
 init(configuration:ReadConfiguration)throws{data=configuration.file.regularFileContents ?? Data()}
 func fileWrapper(configuration:WriteConfiguration)throws->FileWrapper{FileWrapper(regularFileWithContents:data)}
}

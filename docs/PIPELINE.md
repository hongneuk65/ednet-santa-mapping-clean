# Pipeline mới: nguồn → match → tỷ lệ → nhóm cha

## 0. Khóa nguồn và chính sách

Hash mọi file đầu vào; chạy sau khi thay dữ liệu sẽ dừng nếu khác manifest. Snapshot kết quả gồm hash nguồn, config và code pipeline. Không import module ngoài repo, không đọc mapping cũ hoặc gọi mạng.

Các ngưỡng là chính sách khám phá được khai báo trước trong config, không phải ngưỡng bảo đảm accuracy. Taxonomy ánh xạ **mã metadata** sang nhóm cha; không có danh sách EdNet tag ID cài sẵn.

## 1. Chuẩn hóa

Đọc response gốc; giải mã rich text; giữ ID opaque; đáp án single-choice hợp lệ phải là int zero-based trong phạm vi choice. Deduplicate theo ID, kiểm tra xung đột text/choice/đáp án/feature. Bản sao xung đột không được tùy ý chọn làm nguồn match.

## 2. Match câu và bài giảng

Câu phải đạt bốn điều kiện: exact ID, Part, đáp án, tập thành viên bundle chính xác. Xuất cả ID overlap, khớp ba khóa và strict bundle để nhìn thấy ảnh hưởng của từng rào kiểm tra. Rejections được giữ theo từng source variant.

Bài giảng nối lesson ID + Part, giữ title/body/section làm bằng chứng. Part 1 nếu không có question match thì chỉ dùng neo bài giảng, tuyệt đối không coi đó là đọc được câu EdNet.

## 3. Tạo nhãn chữ và nhóm cha

Các trục độc lập:

- task: dạng yêu cầu/câu hỏi.
- grammar: kiến thức ngữ pháp/từ loại/từ vựng.
- topic: chủ đề/bối cảnh nội dung.
- format: dạng hoặc số lượng văn bản.
- accent: thuộc tính giọng đọc, không phải kỹ năng.

Deduplicate mã lặp giữa section/chapter/chapterList. Luật text chỉ dùng stem để nhận dạng nhiệm vụ, không dùng distractor. Chapter/section là metadata cấp content, nên lưu `feature_evidence` và không gắn nhãn gold.

Nhóm cha ví dụ: so sánh; thì; đại từ/từ hạn định; phân từ; nguyên mẫu; bản tin. Không xóa nhánh con hoặc tag nguồn. Một mã có một nhóm cha theo rule có phiên bản; một content có nhiều mã nên có thể đa nhãn và đa trục.

## 4. Đo tỷ lệ theo tag × Part × trục

Với tập câu đã match của tag t, Part p:

- n_bridge: toàn bộ câu đã nối của tag trong Part.
- n_observed: số câu trong n_bridge có dữ liệu ở trục đang xét.
- hits: số câu quan sát mang nhãn ứng viên y.
- P_observed(y|t,p) = hits / n_observed.
- Observability = n_observed / n_bridge.
- Bridge coverage = n_bridge / tổng câu EdNet mang t trong p.
- Recall = hits / số câu quan sát cùng Part mang nhãn y.
- Lift = P_observed / tỷ lệ nền của y trên các câu quan sát cùng Part.

Mọi phép đếm là ID câu khác nhau. Nhãn đa giá trị không bị cộng trùng trên cùng câu. Support bundle đếm bundle khác nhau, không coi ba câu cùng đoạn nghe là ba ngữ cảnh độc lập.

Wilson lower chỉ là interval mô tả với giả định question-IID, không giải quyết phụ thuộc bundle và không phải semantic confidence.

## 5. Gán ứng viên tỷ lệ cao

Lấy ứng viên cao nhất có P_observed >=0,80 và observability >=0,60 theo mỗi tag/Part/trục. Giữ các near-tie trong khoảng <0,10; không chọn tùy ý theo alphabet.

- >=20 câu quan sát và >=10 bundle: `proxy_supported_not_gold`.
- Ít hơn: `provisional_small_support`; dưới 5 câu có cờ small_sample.
- Không có question decision ở trục: có thể dùng metadata bài giảng đồng thuận, trạng thái `lecture_anchor_pending_review`.
- Chỉ có title: giữ evidence, **không tự đặt title thành kỹ năng chi tiết**.

Không dùng câu chưa quan sát để tăng precision. Không gán accent của một Part cho Part khác. Không gọi tỷ lệ proxy là tỷ lệ đúng trên toàn EdNet.

Nếu một tag có neo accent mạnh (>=20 câu, >=10 bundle, ratio >=0,95), giữ tag đó ngoài bước gom kỹ năng. Các tương quan task/topic của tag này được chuyển sang attribute_audit để duyệt, không đặt tên kỹ năng tự động. Đây là rào chống nhầm trục, **không** áp giá trị accent quan sát ở một Part cho mọi Part khác.

## 6. Gom nhóm để thu gọn

Hai loại khác nhau:

1. Tag có cùng nhóm cha chữ: nhóm `same_coarse_label_parent`, giữ scope của từng thành viên. Có thể giao thành viên giữa các trục; đây là phân cấp, không phải tương đương ngữ nghĩa. Không cộng các mức giảm như cluster rời nhau.
2. Tag chưa có mô tả nội dung nhưng có >=5 câu và >=3 bundle: so profile theo Part, không gồm accent. Complete-link similarity >=0,85, tối đa 6 thành viên. Dữ liệu thiếu không được xem như profile giống nhau. Nhóm không có neo nhãn được giữ **chưa đặt tên**, không mượn kỹ năng của hàng xóm.

Profile similarity dùng trung bình hệ số Bhattacharyya trên các trục cùng quan sát. Chỉ là ứng viên khám phá. Chưa có hold-out độc lập hay gold để xác nhận cluster.

## 7. Độ phủ và đánh giá

Đếm lại trên toàn questions.csv theo scope từng Part:

- Có ít nhất một đề xuất nội dung/kỹ năng/định dạng.
- Có bất kỳ mô tả, kể cả accent (báo riêng).
- Mọi tag gốc đều có mô tả nội dung/kỹ năng/định dạng.
- Có nhãn hoặc thuộc nhóm profile chưa đặt tên (báo riêng, không đổi tên thành mapping ngữ nghĩa).

Tag chưa rõ không bị xóa để làm tăng tỷ lệ. Không có gold_accuracy. Trước khi gọi thu gọn “tốt hơn”, cần nhãn kiểm duyệt độc lập và đánh giá downstream trên split độc lập theo người học/bài.

## 8. Notebook và kết quả

Notebook trình bày kiểm kê, funnel nối, mismatch, độ phủ, top tag-label rates, phân bố theo Part, nhóm cha và mẫu cần duyệt. Có cell bật REBUILD để chạy lại từ raw. Markdown kết quả được pipeline sinh sau mỗi lượt; giữ giải thích và giới hạn cùng số liệu.

Kết quả mới có thể khác thí nghiệm trước vì đây là pipeline khác: taxonomy khái quát theo source code, không tái dùng 19 AI review hay danh sách tag đã đặt tên trước. Không cố chỉnh ngưỡng để khớp số 170/172 của lịch sử.

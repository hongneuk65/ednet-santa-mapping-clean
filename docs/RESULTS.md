# Kết quả lượt chạy mới

File sinh từ pipeline hiện tại; không lấy số liệu hoặc nhãn từ báo cáo cũ.

Snapshot: `4b3bc468a01c1bcccae3acac2a27d322fa94360bc98bd121055988b3a6966161`

- EdNet: 13,169 câu, 188 tag.
- Santa: 5,500 lượt câu → 5,470 ID khác nhau.
- Trùng ID: 3,651; khớp ID + Part + đáp án: 3,650; thêm bundle chính xác: 3,648.
- Neo bài giảng ID + Part: 287.
- Tag có đề xuất nội dung/kỹ năng/định dạng: 163; có bất kỳ mô tả (kể cả accent): 168.
- Nhóm cha cùng nhãn thô: 60; nhóm profile chưa đặt tên: 0.

Tag được giữ riêng vì có neo thuộc tính mạnh: 181, 182, 183, 184, 185. Không chuyển giá trị giọng đọc sang Part khác.

## Độ phủ theo Part

Đếm câu có ít nhất một mô tả nội dung/kỹ năng/định dạng áp dụng đúng Part; không tính riêng accent là kỹ năng.

- all: 11844/13169 = 89.94%; mọi tag gốc có mô tả: 7052/13169.
- p1: 589/643 = 91.60%; mọi tag gốc có mô tả: 0/643.
- p2: 1646/1662 = 99.04%; mọi tag gốc có mô tả: 0/1662.
- p3: 1254/1266 = 99.05%; mọi tag gốc có mô tả: 0/1266.
- p4: 1152/1158 = 99.48%; mọi tag gốc có mô tả: 0/1158.
- p5: 5140/5703 = 90.13%; mọi tag gốc có mô tả: 5140/5703.
- p6: 898/1335 = 67.27%; mọi tag gốc có mô tả: 777/1335.
- p7: 1165/1402 = 83.10%; mọi tag gốc có mô tả: 1135/1402.

## Nhóm cha có thể duyệt

Một tag có thể thuộc nhiều trục. Các nhóm có thể giao thành viên; không cộng mức giảm như các cluster rời nhau. Đây là proposal, không phải tương đương đã xác nhận.

- parent:format:advertisement: tag 146, 154; candidate_parent_not_semantic_equivalence.
- parent:format:mail: tag 147, 151, 155, 162, 164, 170; candidate_parent_not_semantic_equivalence.
- parent:format:multi_text: tag 147, 149, 154, 158, 161, 162, 163, 164, 165, 166, 170, 172, 174, 176, 178, 179; candidate_parent_not_semantic_equivalence.
- parent:format:single_text: tag 167, 168, 169, 177; candidate_parent_not_semantic_equivalence.
- parent:format:source:passage_article: tag 157, 161, 165; candidate_parent_not_semantic_equivalence.
- parent:format:source:passage_form: tag 152, 158, 163, 165, 170; candidate_parent_not_semantic_equivalence.
- parent:format:source:passage_notice: tag 159, 164, 166, 174; candidate_parent_not_semantic_equivalence.
- parent:format:source:passage_text: tag 167, 168, 174; candidate_parent_not_semantic_equivalence.
- parent:format:source:passage_webpage: tag 170, 172, 174; candidate_parent_not_semantic_equivalence.
- parent:grammar:comparison: tag 91, 100, 101, 102, 131; candidate_parent_not_semantic_equivalence.
- parent:grammar:connectives: tag 72, 78, 81, 90, 101, 133, 134, 135; candidate_parent_not_semantic_equivalence.
- parent:grammar:gerund: tag 79, 93, 117; candidate_parent_not_semantic_equivalence.
- parent:grammar:infinitive: tag 75, 107, 108, 109, 112, 144; candidate_parent_not_semantic_equivalence.
- parent:grammar:inversion: tag 140, 145; candidate_parent_not_semantic_equivalence.
- parent:grammar:participle: tag 80, 130; candidate_parent_not_semantic_equivalence.
- parent:grammar:preposition: tag 74, 105, 142; candidate_parent_not_semantic_equivalence.
- parent:grammar:pronouns: tag 75, 88, 94, 110, 118; candidate_parent_not_semantic_equivalence.
- parent:grammar:relative: tag 92, 113, 114, 115, 116, 135; candidate_parent_not_semantic_equivalence.
- parent:grammar:source:adjective: tag 84, 101, 114, 129, 132, 134; candidate_parent_not_semantic_equivalence.
- parent:grammar:source:adverb: tag 132, 219; candidate_parent_not_semantic_equivalence.
- parent:grammar:source:agreement: tag 113, 121; candidate_parent_not_semantic_equivalence.
- parent:grammar:source:confusing_adjective: tag 84, 114; candidate_parent_not_semantic_equivalence.
- parent:grammar:source:noun: tag 82, 103, 106; candidate_parent_not_semantic_equivalence.
- parent:grammar:source:verb: tag 89, 111, 123, 124, 126; candidate_parent_not_semantic_equivalence.
- parent:grammar:source:verbid: tag 75, 79, 80, 93, 101, 107, 108, 109, 112, 117, 130, 144; candidate_parent_not_semantic_equivalence.
- parent:grammar:subjunctive: tag 97, 99; candidate_parent_not_semantic_equivalence.
- parent:grammar:tenses: tag 73, 87, 95, 97, 110, 120, 131; candidate_parent_not_semantic_equivalence.
- parent:grammar:vocab_adverb: tag 83, 97; candidate_parent_not_semantic_equivalence.
- parent:grammar:vocab_noun: tag 77, 96; candidate_parent_not_semantic_equivalence.
- parent:grammar:vocab_verb: tag 85, 126, 131, 142; candidate_parent_not_semantic_equivalence.
- parent:grammar:word_position: tag 71, 79, 86, 98, 104, 105, 109, 110, 117, 128, 133, 138; candidate_parent_not_semantic_equivalence.
- parent:task:detail: tag 52, 59, 61, 65, 66, 146, 150, 153, 154, 155, 159, 161, 162, 164, 165, 169, 170, 171, 172, 174, 176, 177, 179; candidate_parent_not_semantic_equivalence.
- parent:task:inference: tag 147, 149, 152, 154, 155, 157, 158, 161, 162, 163, 164, 165, 166, 170, 171, 172, 174, 176, 178, 179; candidate_parent_not_semantic_equivalence.
- parent:task:next_action: tag 54, 69, 156, 170; candidate_parent_not_semantic_equivalence.
- parent:task:p2_choice: tag 44, 45, 49; candidate_parent_not_semantic_equivalence.
- parent:task:p2_how: tag 41, 50; candidate_parent_not_semantic_equivalence.
- parent:task:p2_negative: tag 36, 37; candidate_parent_not_semantic_equivalence.
- parent:task:p2_statement: tag 34, 35, 42; candidate_parent_not_semantic_equivalence.
- parent:task:p2_tag: tag 38, 39; candidate_parent_not_semantic_equivalence.
- parent:task:p2_when: tag 23, 25; candidate_parent_not_semantic_equivalence.
- parent:task:p2_yesno: tag 28, 29, 31, 36, 37, 38, 39, 44, 45, 46, 47, 49; candidate_parent_not_semantic_equivalence.
- parent:task:purpose: tag 148, 174; candidate_parent_not_semantic_equivalence.
- parent:task:source:connection: tag 167, 168, 196; candidate_parent_not_semantic_equivalence.
- parent:task:source:indirect_question: tag 46, 47; candidate_parent_not_semantic_equivalence.
- parent:task:source:passae_review: tag 163, 165, 171; candidate_parent_not_semantic_equivalence.
- parent:task:speaker_intent: tag 57, 168; candidate_parent_not_semantic_equivalence.
- parent:topic:broadcast: tag 61, 66, 69; candidate_parent_not_semantic_equivalence.
- parent:topic:flight_notice: tag 70, 194; candidate_parent_not_semantic_equivalence.
- parent:topic:p1_action: tag 1, 5, 13; candidate_parent_not_semantic_equivalence.
- parent:topic:p1_objects: tag 6, 11, 17, 18; candidate_parent_not_semantic_equivalence.
- parent:topic:p1_observe_pose: tag 8, 9; candidate_parent_not_semantic_equivalence.
- parent:topic:p1_transport: tag 10, 12; candidate_parent_not_semantic_equivalence.
- parent:topic:p1_work_care: tag 3, 4, 16, 180; candidate_parent_not_semantic_equivalence.
- parent:topic:source:broadcast: tag 61, 66, 69; candidate_parent_not_semantic_equivalence.
- parent:topic:source:future: tag 55, 62; candidate_parent_not_semantic_equivalence.
- parent:topic:source:introduction: tag 62, 68; candidate_parent_not_semantic_equivalence.
- parent:topic:source:notice: tag 64, 67, 70, 194; candidate_parent_not_semantic_equivalence.
- parent:topic:source:subject: tag 53, 62; candidate_parent_not_semantic_equivalence.
- parent:topic:source:visual: tag 58, 62; candidate_parent_not_semantic_equivalence.
- parent:topic:telephone: tag 60, 65; candidate_parent_not_semantic_equivalence.

## Chưa chốt

Tag chưa có đề xuất nội dung/kỹ năng/định dạng: 2, 7, 19, 21, 22, 24, 27, 30, 32, 51, 125, 136, 137, 141, 143, 160, 173, 175, 181, 182, 183, 184, 185, 186, 300.

Part 1 không có question bridge. Nhãn từ metadata bài giảng chỉ là neo giả thuyết; chưa xem ảnh/nghe audio hoặc xác minh nội dung lịch sử.
Các tỷ lệ là P(proxy label | tag, Part, observed). Không phải độ chính xác ngữ nghĩa của toàn EdNet. Nhãn ít mẫu được đánh dấu riêng.
Chưa có independent gold hoặc đánh giá downstream. Thu gọn không tự động làm tăng chất lượng.
Duyệt taxonomy và mẫu phản chứng trước khi chốt. Giữ tag gốc để đảo ngược phép chiếu.

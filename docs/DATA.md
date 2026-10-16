# Dữ liệu đầu vào

## Chỉ lấy nguồn, không lấy suy luận cũ

Importer whitelist:

- `data/full/part*/raw/*.json` → `data/raw/santa/full/part*/raw/`.
- `data/supplemental/raw/*.json` → `data/raw/santa/supplemental/raw/`.
- EdNet `contents/questions.csv` và `contents/lectures.csv`.

Mỗi file có đường dẫn nguồn tương đối, dung lượng và SHA256 trong `data/source_manifest.json`.
Không chứa token.txt, .env, catalog phiên học, lịch sử người dùng, payments.csv, coupons.csv, media binaries, dictionary hoặc nhãn quyết định từ thí nghiệm cũ.

## Santa raw

Giữ nguyên response nguồn, không ghi thêm numeric EdNet tag vào file raw:

- `baseContent.contentId`: định danh content.
- `oneOfDomainContent.toeicContent`: Part, chapter, chapterList, sectionList, skill, pronounce (tùy bản ghi).
- `oneOfType.questionSet.questions`: ID, description, objective.choices, oneOfAnswers.andAnswers, explanation, audioResourceId, attachedResourceIds, tagIds.
- `oneOfType.lesson`: ID, title, body, youtubeUrl, tagIds.
- Các content vocabulary được giữ làm nguồn kiểm kê, chưa dùng để suy ra numeric tag của câu.

`andAnswers` là chỉ số zero-based. Không dùng dấu `*` trong choice để đoán đáp án. `tagIds` của Santa giữ riêng; không coi là cùng namespace với tags số EdNet.

## EdNet

`questions.csv`: question_id, bundle_id, correct_answer, part, tags và các metadata hiện có. `lectures.csv`: lecture_id, part, tags, video_length và thời điểm nguồn.
Không có text câu hỏi hoặc ảnh trong hai CSV. `-1` không phải tag đã biết, bị loại khỏi tập numeric tag.

## Khóa nối

Question: Santa id → tiền tố `q`; khớp chuỗi nguyên vẹn, cùng Part, cùng đáp án, và toàn bộ tập question ID trong content bằng tập ID của bundle EdNet. UUID không bị ép lấy phần số để match.

Lecture: Santa lesson.id → tiền tố `l`, cùng Part. Đây là neo metadata, không chứng minh nội dung hiện tại giống thời điểm EdNet thu thập.

Không tải lại website, không gọi API, không ghi đáp án hay tạo phiên học trong repo này.

## Quyền sử dụng

Đây là bản sao nghiên cứu local theo yêu cầu người dùng. Không suy ra quyền tái phân phối công khai nội dung Santa/EdNet. Kiểm tra giấy phép/điều khoản nguồn trước khi chia sẻ raw data hoặc push public.

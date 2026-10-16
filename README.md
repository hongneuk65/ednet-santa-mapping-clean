# EdNet × Santa — source-only mapping

Repo nghiên cứu độc lập: bắt đầu lại từ raw crawl và metadata EdNet, không dùng từ điển tag hay kết quả nối cũ.

## Mục tiêu

1. Kiểm kê dữ liệu có thật.
2. Nối ID câu hỏi, kiểm tra Part, đáp án và thành viên bundle.
3. Theo từng tag/Part, đo tỷ lệ nhãn trong câu đã nối; lấy nhãn có tỷ lệ cao, giữ thiếu dữ liệu và mẫu ít.
4. Gom nhãn chi tiết thành nhóm cha đủ khái quát; thử gom tag yếu bằng profile nhưng không tự đặt tên kỹ năng khi thiếu bằng chứng.
5. Notebook trực quan hóa, xuất JSON/CSV và ghi lại pipeline/kết quả bằng Markdown.

## Cấu trúc

```text
config/                    ngưỡng và taxonomy theo mã metadata, không theo ID tag
data/raw/ednet/             questions.csv, lectures.csv
data/raw/santa/             raw content gốc + supplemental
data/source_manifest.json   danh mục file, SHA256, nguồn tương đối
src/pipeline.py             pipeline viết mới, chỉ đọc dữ liệu trong repo
scripts/                   nhập nguồn, tạo/chạy notebook
notebooks/01_mapping.ipynb  quá trình phân tích với kết quả đã chạy
outputs/                   bảng nối, tỷ lệ, mapping và cluster; sinh lại được
docs/PIPELINE.md            phương pháp và công thức
docs/RESULTS.md             kết quả từ lượt chạy mới
docs/DATA.md                nguồn, trường, phạm vi và quyền sử dụng
tests/                     kiểm tra nối, tỷ lệ, gom nhóm và tính độc lập
```

## Cài và chạy

Python 3.10+; pipeline cốt lõi chỉ cần standard library. Notebook cần các gói trong requirements.txt.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -X utf8 -m src.pipeline
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/create_notebook.py --execute
.\.venv\Scripts\python.exe -m jupyterlab notebooks/01_mapping.ipynb
```

Notebook mặc định đọc output đã sinh. Để tái tính từ nguồn trong notebook, đặt `REBUILD = True` ở cell cấu hình.

Dữ liệu đã được đặt trong repo local này. Chỉ khi cần nhập lại vào checkout mới:

```powershell
python scripts/import_sources.py --source-root D:\NEU\KHOA_LUAN\santa_crawler
```

Importer chỉ lấy raw content và hai CSV EdNet, kiểm tra hash, từ chối ghi đè snapshot khác. Không lấy token, tài khoản, thanh toán, log hoặc mapping cũ. Sau khi có dữ liệu, pipeline không phụ thuộc thư mục cha.

## Cách dùng kết quả

- `outputs/tag_label_rates.csv`: tỷ lệ, support, bridge coverage, recall, lift và ví dụ theo tag/Part/trục.
- `outputs/mapping_decisions.csv`: nhãn ứng viên cao nhất, near-tie và mức hỗ trợ.
- `outputs/tag_mapping.json`: giữ toàn bộ tag gốc, scope, nguồn và nhóm.
- `outputs/clusters.csv`: nhóm cha cùng nhãn hoặc nhóm profile chưa được đặt tên.
- `outputs/ednet_question_mapping.json` / `.csv`: phép chiếu trên đủ câu EdNet, giữ tag gốc, scope và tag còn chưa rõ.
- `docs/RESULTS.md`: số liệu vừa tính; không chép số từ repo trước.

Không gọi mọi nhãn là kỹ năng: tách task, grammar, topic, format và accent. Không tự chuyển nhãn giọng đọc giữa Part. Nhãn metadata cấp content không phải gold câu hỏi; nhãn bài giảng cũng chưa xác minh câu EdNet lịch sử.

## Git và dữ liệu

Repo được chuẩn bị để đồng bộ lên GitHub private `hongneuk65/ednet-santa-mapping-clean`. Raw data, outputs sau xử lý, mapping/cluster, notebook đã chạy và Markdown kết quả đều được version cùng snapshot. Có thể sinh lại outputs bằng pipeline; môi trường ảo, cache và credential không được đưa lên Git.

Chưa gán giấy phép tái phân phối cho nội dung bên thứ ba. Chỉ dùng bản sao local cho nghiên cứu được phép; kiểm tra điều khoản Santa/EdNet trước khi push public, chia sẻ hoặc thêm media. Không bao giờ commit credential.

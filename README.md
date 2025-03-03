# Nexus Artifact Upload Platform

Platform này cho phép bạn upload artifact lên Nexus mirror theo 2 hình thức:

- **Maven**: Sử dụng lệnh `mvn deploy:deploy-file` để upload các artifact theo chuẩn Maven (với file POM hoặc tự generate POM).
- **Raw**: Upload file trực tiếp theo HTTP PUT để duy trì cấu trúc thư mục tương đối.

Tất cả cấu hình được đặt trong file `prop.txt`. Bạn chỉ cần chỉnh sửa file cấu hình và chạy script `upload_mirror.py`.

---

## Nội dung

- [Yêu cầu](#yêu-cầu)
- [Cài đặt](#cài-đặt)
- [Cấu hình](#cấu-hình)
  - [Cấu hình chung](#cấu-hình-chung)
  - [Cấu hình cho upload Maven](#cấu-hình-cho-upload-maven)
  - [Cấu hình cho upload Raw](#cấu-hình-cho-upload-raw)
- [Hướng dẫn sử dụng](#hướng-dẫn-sử-dụng)
- [Ví dụ](#ví-dụ)
- [Khắc phục sự cố](#khắc-phục-sự-cố)

---

## Yêu cầu

- **Python 3.6+**  
- Module [requests](https://pypi.org/project/requests/): Cài đặt bằng lệnh  
  ```bash
  pip install requests
  ```
- **Maven** (nếu sử dụng chế độ Maven upload): Maven cần được cài đặt và cấu hình trong `PATH` hoặc bạn chỉnh sửa biến `mvn_path` trong code.
- **Nexus Repository Manager**:  
  - Nếu sử dụng upload Maven: Cấu hình thông tin xác thực trong file `~/.m2/settings.xml` với `<server>` có `id` trùng với `repoID` được khai báo trong file `prop.txt`.

---

## Cài đặt

1. **Clone hoặc copy các file** vào thư mục làm việc:
   - `upload_mirror.py` (script chính)
   - `prop.txt` (file cấu hình)
2. Cài đặt module requests (nếu chưa):
   ```bash
   pip install requests
   ```

---

## Cấu hình

File `prop.txt` chứa tất cả các thông số cấu hình cho platform. Bạn có thể cấu hình theo 2 kiểu upload:

### Cấu hình chung

- **repo_dirs**: Danh sách các thư mục chứa artifact (cách nhau bởi dấu phẩy).  
  Ví dụ:  
  ```
  repo_dirs=/Users/hoanganh/.m2,/path/to/other/repo
  ```

- **artifact_type**: Loại upload cần thực hiện.  
  - Dùng `maven` để upload artifact theo chuẩn Maven.
  - Dùng `raw` để upload file trực tiếp theo HTTP PUT.  
  Ví dụ:
  ```
  artifact_type=maven
  ```

- **destination**: URL của repository mirror trên Nexus.  
  - Với Maven: URL của repository Maven (ví dụ: `http://localhost:8081/repository/anhnbh-maven-local-v1/`).
  - Với Raw: URL của repository Raw (ví dụ: `http://localhost:8081/repository/raw-mirror/`).

### Cấu hình cho upload Maven

- **repoID**: ID của repository trong Nexus, phải trùng với `<id>` trong file `~/.m2/settings.xml` (nếu Nexus yêu cầu xác thực).  
  Ví dụ:
  ```
  repoID=internal-mirror
  ```

- **groupId** (tuỳ chọn): Nếu không khai báo, mặc định sẽ dùng `default.group`.  
- **version** (tuỳ chọn): Phiên bản artifact, mặc định là `1.0.0`.

Nếu artifact upload bằng Maven không có file đi kèm (jar, war, zip) cùng tên với file POM, thì lệnh deploy sẽ sử dụng tùy chọn `-DgeneratePom=true` để Maven tự sinh POM tối thiểu.

### Cấu hình cho upload Raw

- **file_pattern**: Pattern dùng để quét file trong các thư mục repo. Mặc định là `*` (tất cả file).  
  Ví dụ:
  ```
  file_pattern=*
  ```

- **username** và **password**: Nếu Nexus raw repository yêu cầu xác thực, khai báo username và password tại đây. Nếu không cần, để trống.  
  Ví dụ:
  ```
  username=
  password=
  ```

---

## Hướng dẫn sử dụng

1. **Chỉnh sửa file `prop.txt`**  
   - Cập nhật danh sách thư mục chứa artifact (`repo_dirs`).
   - Chọn kiểu upload qua tham số `artifact_type` (`maven` hoặc `raw`).
   - Cập nhật URL `destination` cho repository mirror.
   - Nếu dùng Maven, đảm bảo khai báo `repoID` và thiết lập thông tin xác thực trong `~/.m2/settings.xml`.
   - Nếu dùng raw, cập nhật `file_pattern` và thông tin xác thực nếu cần.

2. **Chạy script Python**  
   Mở terminal và chạy:
   ```bash
   python3 upload_mirror.py
   ```
   Script sẽ:
   - Đọc cấu hình từ `prop.txt`.
   - Duyệt qua các thư mục được khai báo trong `repo_dirs`.
   - Với **Maven**: Quét các file POM và kiểm tra file đi kèm (jar, war, zip). Sau đó gọi lệnh Maven deploy.
   - Với **Raw**: Quét toàn bộ file theo `file_pattern` và upload qua HTTP PUT, duy trì cấu trúc thư mục tương đối.

3. **Kiểm tra kết quả trên Nexus**  
   - Với Maven: Kiểm tra artifact theo cấu trúc `groupId/artifactId/version`.
   - Với Raw: Kiểm tra cấu trúc thư mục và file đã được upload.

---

## Ví dụ

### File `prop.txt` mẫu cho upload Maven

```properties
# --- CẤU HÌNH CHUNG ---
repo_dirs=/Users/hoanganh/.m2
artifact_type=maven
destination=http://localhost:8081/repository/anhnbh-maven-local-v1/

# --- CẤU HÌNH CHO UPLOAD MAVEN ---
repoID=internal-mirror
groupId=com.example
version=1.0.0
```

### File `prop.txt` mẫu cho upload Raw

```properties
# --- CẤU HÌNH CHUNG ---
repo_dirs=/Users/hoanganh/repo1,/Users/hoanganh/repo2
artifact_type=raw
destination=http://localhost:8081/repository/raw-mirror/
file_pattern=*
username=your_username
password=your_password
```

Sau khi chỉnh sửa, chạy lệnh:
```bash
python3 upload_mirror.py
```

---

## Khắc phục sự cố

- **Lỗi xác thực (401 Unauthorized)**:  
  - Đối với Maven upload: Kiểm tra file `~/.m2/settings.xml` có chứa mục `<server>` với `id` khớp với `repoID` và thông tin xác thực đúng.
  - Đối với Raw upload: Kiểm tra thông tin `username` và `password` trong `prop.txt`.

- **Không tìm thấy file cần upload**:  
  - Kiểm tra giá trị `repo_dirs` và `file_pattern` trong `prop.txt`.
  - Đảm bảo các thư mục chứa file tồn tại và có quyền truy cập.

- **Lỗi mạng hoặc URL không hợp lệ**:  
  - Kiểm tra lại giá trị `destination` để đảm bảo URL repository đúng và có thể truy cập được từ máy bạn.

---

## Kết luận

Platform này cho phép bạn dễ dàng upload đa dạng loại file lên Nexus mirror chỉ qua cấu hình trong file `prop.txt`. Nếu có bất kỳ vấn đề hoặc cần mở rộng thêm tính năng, bạn có thể điều chỉnh code trong `upload_mirror.py` theo nhu cầu.

Chúc bạn thành công!

---

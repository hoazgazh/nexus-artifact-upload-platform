import sys
import os
import subprocess
import requests
from pathlib import Path

def read_properties(fname):
    """
    Đọc file cấu hình dạng key=value,
    bỏ qua dòng trống và dòng bắt đầu bằng #
    """
    props = {}
    if not os.path.isfile(fname):
        print(f"File cấu hình '{fname}' không tồn tại!")
        sys.exit(1)
    with open(fname, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                props[key.strip()] = value.strip()
    return props

def process_maven(props):
    """
    Upload artifact theo chuẩn Maven.
    Code sẽ duyệt qua các thư mục được khai báo trong repo_dirs,
    quét các file POM (sử dụng rglob("*.pom")), sau đó:
      - Nếu có file kèm theo (jar, war, zip) cùng tên thì dùng file đó.
      - Nếu không, sẽ upload file POM và dùng lệnh -DgeneratePom=true.
    Các toạ độ Maven được lấy từ file prop.txt:
      groupId, version được dùng chung,
      artifactId được lấy từ tên file POM (stem) nếu không có cấu hình riêng.
    """
    repo_dirs = props.get("repo_dirs", "")
    if not repo_dirs:
        print("Chưa khai báo repo_dirs trong prop.txt")
        sys.exit(1)
    repo_dirs = [s.strip() for s in repo_dirs.split(",") if s.strip()]
    
    destination = props.get("destination", "").strip()
    repoID = props.get("repoID", "").strip()
    groupId = props.get("groupId", "default.group").strip()
    version = props.get("version", "1.0.0").strip()

    if not destination or not repoID:
        print("Thiếu destination hoặc repoID trong cấu hình cho Maven")
        sys.exit(1)

    # Sử dụng mvn trong PATH hoặc chỉ rõ đường dẫn (nếu cần)
    mvn_path = "mvn"

    total = 0
    for repo_dir in repo_dirs:
        base_path = Path(repo_dir)
        if not base_path.is_dir():
            print(f"Directory '{repo_dir}' không tồn tại hoặc không phải thư mục.")
            continue

        print(f"\nQuét thư mục (Maven): {base_path}")
        # Quét các file POM
        for pom_path in base_path.rglob("*.pom"):
            if not pom_path.is_file():
                continue

            artifactId = pom_path.stem  # Dùng tên file (không có .pom) làm artifactId

            # Kiểm tra các file đi kèm: jar, war, zip
            file_to_upload = None
            packaging = "pom"  # mặc định
            for ext in ["jar", "war", "zip"]:
                candidate = pom_path.with_suffix("." + ext)
                if candidate.exists():
                    file_to_upload = candidate
                    packaging = ext
                    break
            if not file_to_upload:
                # Nếu không tìm thấy file đi kèm, dùng chính file POM
                file_to_upload = pom_path
                packaging = "pom"

            # Nếu file được dùng là chính file POM và không phải jar/war/zip, ta dùng -DgeneratePom=true
            generatePom = "true" if packaging == "pom" else "false"

            cmd = [
                mvn_path, "deploy:deploy-file",
                f"-Dfile={str(file_to_upload)}",
                f"-DgroupId={groupId}",
                f"-DartifactId={artifactId}",
                f"-Dversion={version}",
                f"-Dpackaging={packaging}",
                f"-DrepositoryId={repoID}",
                f"-Durl={destination}",
                f"-DgeneratePom={generatePom}"
            ]

            print("\n------------------------------------------------------------")
            print("Thực thi lệnh:")
            print(" ".join(cmd))
            result = subprocess.run(cmd, shell=False)
            if result.returncode == 0:
                print(f"Upload thành công: {file_to_upload}")
                total += 1
            else:
                print(f"Upload thất bại: {file_to_upload}")
    print(f"\nTổng số artifact (Maven) đã upload: {total}")

def process_raw(props):
    """
    Upload file theo kiểu raw (HTTP PUT) để đẩy file không theo chuẩn Maven.
    Code sẽ duyệt qua các thư mục khai báo trong repo_dirs và upload toàn bộ file
    (theo file_pattern) lên destination, duy trì cấu trúc thư mục tương đối.
    Nếu cần xác thực, dùng username và password.
    """
    repo_dirs = props.get("repo_dirs", "")
    if not repo_dirs:
        print("Chưa khai báo repo_dirs trong prop.txt")
        sys.exit(1)
    repo_dirs = [s.strip() for s in repo_dirs.split(",") if s.strip()]

    destination = props.get("destination", "").strip()
    if not destination:
        print("Chưa khai báo destination cho raw upload")
        sys.exit(1)

    file_pattern = props.get("file_pattern", "*").strip()
    username = props.get("username", "").strip()
    password = props.get("password", "").strip()
    auth = (username, password) if username and password else None

    total = 0
    for repo_dir in repo_dirs:
        base_path = Path(repo_dir)
        if not base_path.is_dir():
            print(f"Directory '{repo_dir}' không tồn tại hoặc không phải thư mục.")
            continue

        print(f"\nQuét thư mục (Raw): {base_path}")
        for file_path in base_path.rglob(file_pattern):
            if file_path.is_file():
                try:
                    relative_path = file_path.relative_to(base_path)
                except ValueError:
                    relative_path = file_path.name
                relative_url = str(relative_path).replace(os.sep, "/")
                url = destination.rstrip("/") + "/" + relative_url

                print(f"\nUploading '{file_path}' -> {url}")
                headers = {"Content-Type": "application/octet-stream"}
                try:
                    with open(file_path, "rb") as f:
                        data = f.read()
                except Exception as e:
                    print(f"Lỗi đọc file {file_path}: {e}")
                    continue

                try:
                    response = requests.put(url, data=data, headers=headers, auth=auth)
                except Exception as e:
                    print(f"Lỗi khi upload {file_path}: {e}")
                    continue

                if response.status_code in [200, 201, 204]:
                    print(f"Upload thành công: {file_path}")
                    total += 1
                else:
                    print(f"Upload thất bại {file_path}: HTTP {response.status_code} - {response.text}")
    print(f"\nTổng số file đã upload (Raw): {total}")

def main():
    props = read_properties("prop.txt")
    artifact_type = props.get("artifact_type", "raw").strip().lower()

    if artifact_type == "maven":
        process_maven(props)
    else:
        # Với artifact_type là raw, jar, war, zip, ant, ... ta sử dụng phương thức raw upload
        process_raw(props)

if __name__ == "__main__":
    main()

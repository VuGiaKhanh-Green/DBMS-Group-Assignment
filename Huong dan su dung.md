# Hướng dẫn sử dụng

+ Bước 1 : Làm theo file báo cáo (Group01's Report.pdf) để thực hiện setup cơ sở dữ liệu,tạo cơ sở dữ liệu không gian
+ Bước 2 : Tải 2 file app.python và index.html về và để chúng trong cùng 1 thư mục(recommend để trong ổ D )
+ Bước 3 : Mở cmd lên để dựng backend API dùng python
```cmd
pip install flask flask-cors psycopg2-binary
```
+ Bước 3 : Tạo GeoJSON trong PostgreSQL
```postgresql
    SELECT json_build_object(
    'type', 'FeatureCollection',
    'features', json_agg(ST_AsGeoJSON(t.*)::json)
) AS geojson_data
FROM building AS t;
SELECT json_build_object(
    'type', 'FeatureCollection',
    'features', json_agg(ST_AsGeoJSON(t.*)::json)
) AS geojson_data
FROM road AS t;
SELECT json_build_object(
    'type', 'FeatureCollection',
    'features', json_agg(ST_AsGeoJSON(t.*)::json)
) AS geojson_data
FROM bound AS t;
SELECT json_build_object(
    'type', 'FeatureCollection',
    'features', json_agg(ST_AsGeoJSON(t.*)::json)
) AS geojson_data
FROM garbadge AS t;
```
+ Bước 4 : Mở Terminal tại thư mục chứa 2 file trên và gõ lệnh
```cmd
python app.py
```
Nếu như hiện ra dòng chữ 
```cmd
Running on http://127.0.0.1:5000
```
-> đã chạy thành công

Sau đó click đúp vào index.html lên để chạy file trên trình duyệt


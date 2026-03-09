from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app) 

@app.route('/api/spatial-data', methods=['GET'])
def get_spatial_data():
    try:
        # NHỚ ĐIỀN LẠI DBNAME VÀ PASSWORD CỦA BẠN
        conn = psycopg2.connect(
            dbname="BC", 
            user="postgres",               
            password="123456",   
            host="localhost",
            port="5432"                    
        )
        cur = conn.cursor()

        # Đã thêm đủ 5 bảng của bạn
        bang_du_lieu = ['bounds', 'instruction-generated', 'road', 'building', 'garbadge']
        ket_qua = {}

        for bang in bang_du_lieu:
            # Dùng "{bang}" (có ngoặc kép) để tránh lỗi với bảng instruction-generated
            sql_query = f"""
                SELECT json_build_object(
                    'type', 'FeatureCollection',
                    'features', COALESCE(json_agg(
                        json_build_object(
                            'type',       'Feature',
                            'geometry',   ST_AsGeoJSON(ST_Transform(ST_SetSRID(geom, 3857), 4326))::json,
                            'properties', to_jsonb(t.*) - 'geom'
                        )
                    ), '[]'::json)
                ) AS geojson_data
                FROM "{bang}" AS t;
            """
            cur.execute(sql_query)
            ket_qua[bang] = cur.fetchone()[0]
        
        cur.close()
        conn.close()

        return jsonify(ket_qua)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```sql
-- 1. VIEW NGƯỜI THUÊ (Danh sách khách hàng đang thuê)
CREATE OR REPLACE VIEW vw_NguoiThue AS
SELECT k.CCCD, k.HoTen, k.QueQuan, h.MaPhong, h.NgayKy, h.TrangThai
FROM KhachHang k
JOIN HopDong h ON k.CCCD = h.CCCD
WHERE h.TrangThai = 'Còn hiệu lực';

-- 2. VIEW PHÒNG (Tình trạng các phòng)
CREATE OR REPLACE VIEW vw_TinhTrangPhong AS
SELECT MaPhong, DienTich, TrangThai
FROM PhongTro;

-- 3. VIEW DANH SÁCH HỢP ĐỒNG
CREATE OR REPLACE VIEW vw_DanhSachHopDong AS
SELECT h.MaHD, k.HoTen, h.MaPhong, h.NgayKy, h.ThoiHan, h.TienCoc, h.TrangThai
FROM HopDong h
JOIN KhachHang k ON h.CCCD = k.CCCD;

-- 4. VIEW NGƯỜI CÒN NỢ TIỀN
CREATE OR REPLACE VIEW vw_NguoiNoTien AS
SELECT hd.MaBill, k.HoTen, p.MaPhong, hd.TongTien, 
       COALESCE(SUM(pt.DaThu), 0) AS DaThanhToan,
       (hd.TongTien - COALESCE(SUM(pt.DaThu), 0)) AS ConNo
FROM HoaDon hd
JOIN HopDong h ON hd.MaHD = h.MaHD
JOIN KhachHang k ON h.CCCD = k.CCCD
JOIN PhongTro p ON h.MaPhong = p.MaPhong
LEFT JOIN PhieuThu pt ON hd.MaBill = pt.MaBill
GROUP BY hd.MaBill, k.HoTen, p.MaPhong, hd.TongTien
HAVING ConNo > 0;

-- 5. VIEW DOANH THU THEO KỲ HÓA ĐƠN[cite: 3]
CREATE OR REPLACE VIEW vw_DoanhThu AS
SELECT KyHoaDon, SUM(DaThu) AS TongDoanhThuThucTe
FROM PhieuThu pt
JOIN HoaDon hd ON pt.MaBill = hd.MaBill
GROUP BY KyHoaDon;

-- 6. VIEW THUẾ DỰA TRÊN DOANH THU (Giả sử 5%)[cite: 3]
CREATE OR REPLACE VIEW vw_ThueDoanhThu AS
SELECT KyHoaDon, TongDoanhThuThucTe, 
       (TongDoanhThuThucTe * 0.05) AS ThuePhaiNop
FROM vw_DoanhThu;
```

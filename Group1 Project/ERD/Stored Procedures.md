```sql
DELIMITER //

-- 1. THÊM HỢP ĐỒNG MỚI (Tự động cập nhật trạng thái phòng)[cite: 3]
CREATE PROCEDURE sp_ThemHopDong(
    IN p_MaHD VARCHAR(15), IN p_CCCD CHAR(12), 
    IN p_MaPhong VARCHAR(10), IN p_ThoiHan INT, IN p_TienCoc DECIMAL(15,2)
)
BEGIN
    INSERT INTO HopDong(MaHD, CCCD, MaPhong, ThoiHan, TienCoc, TrangThai)
    VALUES (p_MaHD, p_CCCD, p_MaPhong, p_ThoiHan, p_TienCoc, 'Còn hiệu lực');
    
    UPDATE PhongTro SET TrangThai = 'Đang được thuê' WHERE MaPhong = p_MaPhong;
END //

-- 2. HỦY HỢP ĐỒNG (Giải phóng phòng trống ngay lập tức)[cite: 3]
CREATE PROCEDURE sp_HuyHopDong(IN p_MaHD VARCHAR(15))
BEGIN
    DECLARE v_MaPhong VARCHAR(10);
    SELECT MaPhong INTO v_MaPhong FROM HopDong WHERE MaHD = p_MaHD;
    
    UPDATE HopDong SET TrangThai = 'Bị hủy bỏ' WHERE MaHD = p_MaHD;
    UPDATE PhongTro SET TrangThai = 'Còn trống' WHERE MaPhong = v_MaPhong;
END //

-- 3. TẠO HÓA ĐƠN (Tự động cộng dồn tiền phòng và dịch vụ)[cite: 3]
CREATE PROCEDURE sp_TaoHoaDon(IN p_MaBill VARCHAR(20), IN p_MaHD VARCHAR(15), IN p_KyHoaDon VARCHAR(10))
BEGIN
    DECLARE v_TienPhong DECIMAL(15,2);
    DECLARE v_TienDichVu DECIMAL(15,2);
    DECLARE v_TongTien DECIMAL(15,2);

    -- Lấy giá phòng mới nhất[cite: 3]
    SELECT GiaTien INTO v_TienPhong FROM GiaPhong 
    WHERE MaHD = p_MaHD ORDER BY NgayAp DESC LIMIT 1;
      
    -- Lấy tổng tiền dịch vụ khách đã đăng ký[cite: 3]
    SELECT COALESCE(SUM(SoLuong * DonGia), 0) INTO v_TienDichVu 
    FROM DangKyDichVu WHERE MaHD = p_MaHD;
      
    SET v_TongTien = v_TienPhong + v_TienDichVu;

    INSERT INTO HoaDon(MaBill, MaHD, TongTien, KyHoaDon, TrangThai)
    VALUES (p_MaBill, p_MaHD, v_TongTien, p_KyHoaDon, 'Còn thiếu');
      
    INSERT INTO ChiTietHoaDon(MaBill, Loai, MoTaChiTiet, DonGia, SoLuong)
    VALUES (p_MaBill, 'TienPhong', 'Tiền thuê phòng', v_TienPhong, 1);
END //

DELIMITER ;
```

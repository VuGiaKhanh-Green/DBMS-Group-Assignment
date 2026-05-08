```sql
DELIMITER //

-- 1. THÊM HỢP ĐỒNG MỚI (Tự động cập nhật trạng thái phòng)
CREATE PROCEDURE sp_ThemHopDong(
    IN p_MaHD VARCHAR(15), 
    IN p_CCCD CHAR(12), 
    IN p_MaPhong VARCHAR(10), 
    IN p_ThoiHan INT, 
    IN p_TienCoc DECIMAL(15,2),
    IN p_GiaThue DECIMAL(15,2)
)
BEGIN
    -- Thêm hợp đồng
    INSERT INTO HopDong(MaHD, CCCD, MaPhong, ThoiHan, TienCoc, TrangThai)
    VALUES (p_MaHD, p_CCCD, p_MaPhong, p_ThoiHan, p_TienCoc, 'Còn hiệu lực');
    
    -- Cập nhật trạng thái phòng
    UPDATE PhongTro SET TrangThai = 'Đang được thuê' WHERE MaPhong = p_MaPhong;
    
    -- Tạo bản ghi giá thuê đầu tiên (lần đổi đầu tiên)
    INSERT INTO GiaPhong (MaHD, GiaTien, NgayAp)
    VALUES (p_MaHD, p_GiaThue, CURRENT_DATE);
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
CREATE OR REPLACE PROCEDURE sp_TaoHoaDon(
    IN p_MaBill VARCHAR(20), 
    IN p_MaHD VARCHAR(15), 
    IN p_KyHoaDon VARCHAR(10)
)
BEGIN
    DECLARE v_TienPhong DECIMAL(15,2) DEFAULT 0;
    DECLARE v_TienDichVu DECIMAL(15,2) DEFAULT 0;
    DECLARE v_TongTien DECIMAL(15,2) DEFAULT 0;

    -- Tiền phòng (giá mới nhất)
    SELECT GiaTien INTO v_TienPhong 
    FROM GiaPhong 
    WHERE MaHD = p_MaHD 
    ORDER BY NgayAp DESC 
    LIMIT 1;

    -- Tiền dịch vụ bắt buộc
    SELECT COALESCE(SUM(dk.SoLuong * dk.DonGia), 0) INTO v_TienDichVu
    FROM DangKyDichVu dk
    JOIN DichVu dv ON dk.MaDV = dv.MaDV
    WHERE dk.MaHD = p_MaHD AND dv.LoaiDV = 'Bắt buộc';

    -- Cộng thêm tiền dịch vụ tự chọn (còn hiệu lực)
    SELECT v_TienDichVu + COALESCE(SUM(dk.SoLuong * dk.DonGia), 0) INTO v_TienDichVu
    FROM DangKyDichVu dk
    JOIN DichVu dv ON dk.MaDV = dv.MaDV
    WHERE dk.MaHD = p_MaHD 
      AND dv.LoaiDV = 'Lựa chọn'
      AND dk.ThangBD <= CURRENT_DATE 
      AND dk.ThangKT >= CURRENT_DATE;

    SET v_TongTien = v_TienPhong + v_TienDichVu;

    -- Chèn hóa đơn
    INSERT INTO HoaDon(MaBill, MaHD, TongTien, KyHoaDon, TrangThai)
    VALUES (p_MaBill, p_MaHD, v_TongTien, p_KyHoaDon, 'Còn thiếu');

    -- Chèn chi tiết hóa đơn (chỉ 1 dòng cho tiền phòng, 1 dòng cho tiền dịch vụ nếu có)
    INSERT INTO ChiTietHoaDon (MaBill, Loai, MoTaChiTiet, DonGia, SoLuong)
    VALUES (p_MaBill, 'TienPhong', 'Tiền thuê phòng', v_TienPhong, 1);

    IF v_TienDichVu > 0 THEN
        INSERT INTO ChiTietHoaDon (MaBill, Loai, MoTaChiTiet, DonGia, SoLuong)
        VALUES (p_MaBill, 'TienDichVu', 'Dịch vụ (bắt buộc + tự chọn)', v_TienDichVu, 1);
    END IF;
END //
DELIMITER ;

```

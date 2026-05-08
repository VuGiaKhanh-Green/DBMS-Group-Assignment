```sql
DELIMITER //

-- 1. THÊM HỢP ĐỒNG MỚI 
CREATE PROCEDURE sp_ThemHopDong(
    IN p_MaHD VARCHAR(15), 
    IN p_CCCD CHAR(12), 
    IN p_HoTen VARCHAR(100),
    IN p_QueQuan VARCHAR(200),
    IN p_MaPhong VARCHAR(10), 
    IN p_ThoiHan INT, 
    IN p_TienCoc DECIMAL(15,2),
    IN p_GiaThue DECIMAL(15,2)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;   -- Trả lại lỗi cho client
    END;

    START TRANSACTION;

    -- 1. Kiểm tra và thêm/cập nhật khách hàng
    IF NOT EXISTS (SELECT 1 FROM KhachHang WHERE CCCD = p_CCCD) THEN
        INSERT INTO KhachHang (CCCD, HoTen, QueQuan) VALUES (p_CCCD, p_HoTen, p_QueQuan);
    ELSE
        UPDATE KhachHang SET HoTen = p_HoTen, QueQuan = p_QueQuan WHERE CCCD = p_CCCD;
    END IF;

    -- 2. Kiểm tra khách có hợp đồng đang hiệu lực không
    IF EXISTS (SELECT 1 FROM HopDong WHERE CCCD = p_CCCD AND TrangThai = 'Còn hiệu lực') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Khách đã có hợp đồng đang hiệu lực, không thể thêm mới';
    END IF;

    -- 3. Thêm hợp đồng
    INSERT INTO HopDong(MaHD, CCCD, MaPhong, ThoiHan, TienCoc, TrangThai)
    VALUES (p_MaHD, p_CCCD, p_MaPhong, p_ThoiHan, p_TienCoc, 'Còn hiệu lực');

    -- 4. Cập nhật trạng thái phòng
    UPDATE PhongTro SET TrangThai = 'Đang được thuê' WHERE MaPhong = p_MaPhong;

    -- 5. Ghi nhận giá thuê đầu tiên
    INSERT INTO GiaPhong (MaHD, GiaTien, NgayAp)
    VALUES (p_MaHD, p_GiaThue, CURDATE());

    COMMIT;
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
CREATE PROCEDURE sp_TaoHoaDon(
    IN p_MaBill VARCHAR(20), 
    IN p_MaHD VARCHAR(15), 
    IN p_KyHoaDon VARCHAR(10)
)
BEGIN
    DECLARE v_TienPhong DECIMAL(15,2) DEFAULT 0;
    DECLARE v_TienDichVu DECIMAL(15,2) DEFAULT 0;
    DECLARE v_TongTien DECIMAL(15,2) DEFAULT 0;

    -- Tiền phòng mới nhất
    SELECT GiaTien INTO v_TienPhong 
    FROM GiaPhong 
    WHERE MaHD = p_MaHD 
    ORDER BY NgayAp DESC LIMIT 1;

    -- Dịch vụ bắt buộc (không phụ thuộc thời hạn, nhưng thêm TrangThai cho chắc)
    SELECT COALESCE(SUM(dk.SoLuong * dk.DonGia), 0) INTO v_TienDichVu
    FROM DangKyDichVu dk
    JOIN DichVu dv ON dk.MaDV = dv.MaDV
    WHERE dk.MaHD = p_MaHD 
      AND dv.LoaiDV = 'Bắt buộc'
      AND dk.TrangThai = 'Còn hiệu lực';

    -- Dịch vụ tự chọn còn hiệu lực và trong thời gian
    SELECT v_TienDichVu + COALESCE(SUM(dk.SoLuong * dk.DonGia), 0) INTO v_TienDichVu
    FROM DangKyDichVu dk
    JOIN DichVu dv ON dk.MaDV = dv.MaDV
    WHERE dk.MaHD = p_MaHD 
      AND dv.LoaiDV = 'Lựa chọn'
      AND dk.ThangBD <= CURDATE() 
      AND dk.ThangKT >= CURDATE()
      AND dk.TrangThai = 'Còn hiệu lực';

    SET v_TongTien = v_TienPhong + v_TienDichVu;

    INSERT INTO HoaDon(MaBill, MaHD, TongTien, KyHoaDon, TrangThai)
    VALUES (p_MaBill, p_MaHD, v_TongTien, p_KyHoaDon, 'Còn thiếu');

    INSERT INTO ChiTietHoaDon (MaBill, Loai, MoTaChiTiet, DonGia, SoLuong)
    VALUES (p_MaBill, 'TienPhong', 'Tiền thuê phòng', v_TienPhong, 1);

    IF v_TienDichVu > 0 THEN
        INSERT INTO ChiTietHoaDon (MaBill, Loai, MoTaChiTiet, DonGia, SoLuong)
        VALUES (p_MaBill, 'TienDichVu', 'Dịch vụ (bắt buộc + tự chọn)', v_TienDichVu, 1);
    END IF;
END //
 -- đăng ký dịch vụ

CREATE PROCEDURE sp_DangKyDichVu(
    IN p_MaHD VARCHAR(15),
    IN p_MaDV VARCHAR(10),
    IN p_ThangBD DATE,
    IN p_ThangKT DATE,
    IN p_SoLuong INT,
    IN p_DonGia DECIMAL(15,2)
)
BEGIN
    DECLARE v_LoaiDV VARCHAR(50);

    -- Kiểm tra hợp đồng tồn tại và còn hiệu lực
    IF NOT EXISTS (SELECT 1 FROM HopDong WHERE MaHD = p_MaHD AND TrangThai = 'Còn hiệu lực') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Hợp đồng không tồn tại hoặc không còn hiệu lực';
    END IF;

    -- Lấy loại dịch vụ
    SELECT LoaiDV INTO v_LoaiDV FROM DichVu WHERE MaDV = p_MaDV;
    IF v_LoaiDV IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Mã dịch vụ không tồn tại';
    END IF;
    IF v_LoaiDV != 'Lựa chọn' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Chỉ được đăng ký dịch vụ tự chọn';
    END IF;

    -- Thêm mới đăng ký
    INSERT INTO DangKyDichVu (MaHD, MaDV, ThangBD, ThangKT, SoLuong, DonGia, TrangThai)
    VALUES (p_MaHD, p_MaDV, p_ThangBD, p_ThangKT, p_SoLuong, p_DonGia, 'Còn hiệu lực');
END //
-- Hủy dịch vụ

CREATE PROCEDURE sp_HuyDichVu(IN p_MaDK INT)
BEGIN
    DECLARE v_MaHD VARCHAR(15);
    DECLARE v_TrangThai VARCHAR(50);

    -- Kiểm tra tồn tại
    SELECT MaHD, TrangThai INTO v_MaHD, v_TrangThai
    FROM DangKyDichVu WHERE MaDK = p_MaDK;

    IF v_MaHD IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Mã đăng ký không tồn tại';
    END IF;

    -- Chỉ hủy khi đang "Còn hiệu lực"
    IF v_TrangThai != 'Còn hiệu lực' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Dịch vụ này đã bị hủy trước đó';
    END IF;

    -- Cập nhật trạng thái
    UPDATE DangKyDichVu SET TrangThai = 'Đã hủy' WHERE MaDK = p_MaDK;
END //
DELIMITER ;

```

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
CREATE OR REPLACE PROCEDURE sp_HuyHopDong(IN p_MaHD VARCHAR(15))
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Lấy thông tin
    SELECT MaPhong INTO @v_MaPhong FROM HopDong WHERE MaHD = p_MaHD;
    SELECT TrangThai INTO @v_TrangThai FROM HopDong WHERE MaHD = p_MaHD;

    IF @v_MaPhong IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Hợp đồng không tồn tại';
    END IF;
    IF @v_TrangThai != 'Còn hiệu lực' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Hợp đồng không còn hiệu lực để hủy';
    END IF;

    UPDATE HopDong SET TrangThai = 'Bị hủy bỏ' WHERE MaHD = p_MaHD;

    -- Giải phóng phòng nếu không còn hợp đồng hiệu lực khác
    IF NOT EXISTS (
        SELECT 1 FROM HopDong 
        WHERE MaPhong = @v_MaPhong 
          AND TrangThai = 'Còn hiệu lực'
          AND MaHD != p_MaHD
    ) THEN
        UPDATE PhongTro SET TrangThai = 'Còn trống' WHERE MaPhong = @v_MaPhong;
    END IF;

    COMMIT;
END //

-- 3. Hủy dịch vụ

CREATE OR REPLACE PROCEDURE sp_HuyDichVu(IN p_MaDK INT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT MaHD, TrangThai INTO @v_MaHD, @v_TrangThai FROM DangKyDichVu WHERE MaDK = p_MaDK;
    IF @v_MaHD IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Mã đăng ký không tồn tại';
    END IF;
    IF @v_TrangThai != 'Còn hiệu lực' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Dịch vụ này đã bị hủy trước đó';
    END IF;

    UPDATE DangKyDichVu SET TrangThai = 'Đã hủy' WHERE MaDK = p_MaDK;

    COMMIT;
END //
--- 4. ĐĂNG KÝ DỊCH VỤ
CREATE OR REPLACE PROCEDURE sp_DangKyDichVu(
    IN p_MaHD VARCHAR(15),
    IN p_MaDV VARCHAR(10),
    IN p_ThangBD DATE,
    IN p_ThangKT DATE,
    IN p_SoLuong INT,
    IN p_DonGia DECIMAL(15,2)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Kiểm tra hợp đồng
    IF NOT EXISTS (SELECT 1 FROM HopDong WHERE MaHD = p_MaHD AND TrangThai = 'Còn hiệu lực') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Hợp đồng không tồn tại hoặc không còn hiệu lực';
    END IF;

    -- Kiểm tra dịch vụ
    SELECT LoaiDV INTO @v_LoaiDV FROM DichVu WHERE MaDV = p_MaDV;
    IF @v_LoaiDV IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Mã dịch vụ không tồn tại';
    END IF;
    IF @v_LoaiDV != 'Lựa chọn' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Chỉ được đăng ký dịch vụ tự chọn';
    END IF;

    INSERT INTO DangKyDichVu (MaHD, MaDV, ThangBD, ThangKT, SoLuong, DonGia, TrangThai)
    VALUES (p_MaHD, p_MaDV, p_ThangBD, p_ThangKT, p_SoLuong, p_DonGia, 'Còn hiệu lực');

    COMMIT;
END //

-- 5. TẠO HÓA ĐƠN (Tự động cộng dồn tiền phòng và dịch vụ)[cite: 3]
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
    -- Tiền dịch vụ bắt buộc (không cần thời hạn)
    SELECT COALESCE(SUM(dk.SoLuong * dk.DonGia), 0) INTO v_TienDVBatBuoc
    FROM DangKyDichVu dk
    JOIN DichVu dv ON dk.MaDV = dv.MaDV
    WHERE dk.MaHD = p_MaHD AND dv.LoaiDV = 'Bắt buộc';

    -- Tiền dịch vụ tự chọn (có kiểm tra thời hạn hiệu lực)
    SELECT COALESCE(SUM(dk.SoLuong * dk.DonGia), 0) INTO v_TienDVTuChon
    FROM DangKyDichVu dk
    JOIN DichVu dv ON dk.MaDV = dv.MaDV
    WHERE dk.MaHD = p_MaHD 
      AND dv.LoaiDV = 'Lựa chọn'
      AND dk.ThangBD <= CURRENT_DATE 
      AND dk.ThangKT >= CURRENT_DATE;

    SET v_TongTien = v_TienPhong + v_TienDVBatBuoc + v_TienDVTuChon;

    -- Thêm hóa đơn
    INSERT INTO HoaDon(MaBill, MaHD, TongTien, KyHoaDon, TrangThai)
    VALUES (p_MaBill, p_MaHD, v_TongTien, p_KyHoaDon, 'Còn thiếu');
      
    INSERT INTO ChiTietHoaDon(MaBill, Loai, MoTaChiTiet, DonGia, SoLuong)

    -- Thêm chi tiết hóa đơn
    INSERT INTO ChiTietHoaDon (MaBill, Loai, MoTaChiTiet, DonGia, SoLuong)
    VALUES (p_MaBill, 'TienPhong', 'Tiền thuê phòng', v_TienPhong, 1);

    IF v_TienDVBatBuoc > 0 THEN
        INSERT INTO ChiTietHoaDon (MaBill, Loai, MoTaChiTiet, DonGia, SoLuong)
        VALUES (p_MaBill, 'TienDichVu', 'Dịch vụ bắt buộc', v_TienDVBatBuoc, 1);
    END IF;

    IF v_TienDVTuChon > 0 THEN
        INSERT INTO ChiTietHoaDon (MaBill, Loai, MoTaChiTiet, DonGia, SoLuong)
        VALUES (p_MaBill, 'TienDichVu', 'Dịch vụ tự chọn', v_TienDVTuChon, 1);
    END IF;
END //
DELIMITER ;

```

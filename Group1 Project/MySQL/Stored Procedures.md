```sql
DELIMITER //

CREATE PROCEDURE sp_TaoHoaDon(
    IN p_MaBill VARCHAR(20), 
    IN p_MaHD VARCHAR(15), 
    IN p_KyHoaDon VARCHAR(10)
)
BEGIN
    DECLARE v_TienPhong DECIMAL(15,2) DEFAULT 0;
    DECLARE v_TienDVBatBuoc DECIMAL(15,2) DEFAULT 0;
    DECLARE v_TienDVTuChon DECIMAL(15,2) DEFAULT 0;
    DECLARE v_TongTien DECIMAL(15,2) DEFAULT 0;

    -- Tiền phòng: lấy giá mới nhất
    SELECT GiaTien INTO v_TienPhong 
    FROM GiaPhong 
    WHERE MaHD = p_MaHD 
    ORDER BY NgayAp DESC 
    LIMIT 1;

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

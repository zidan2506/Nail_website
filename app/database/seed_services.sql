-- ============================================================
-- SEED TEST: services
-- DahaCare Nail Salon
-- Prices incl. 25.5% VAT | Points: 1 EUR = 1 point
--
-- ⚠️ PHỤ THUỘC: cần seed.sql chạy TRƯỚC (service_categories id 1/2/3).
--    Chạy bằng: python -m app.init_db --seed-services
--
-- image: path tĩnh dưới /static/ — _resolve_upload() trong routes.py thấy
--        prefix '/' thì dùng thẳng, không đụng tới uploads/.
-- ============================================================

-- ------------------------------------------------------------
-- services — Manicure (category_id = 1)
-- ------------------------------------------------------------
INSERT INTO services (
    category_id,
    name, name_vi, name_fi,
    description, description_vi, description_fi,
    duration_minutes, price, points,
    badge, icon, image, is_active
) VALUES

-- 1. Classic Manicure
(
    1,
    'Classic Manicure',
    'Làm móng cơ bản',
    'Perusmanikyyri',
    'Nail shaping, cuticle care, buffing and classic polish for clean, natural-looking nails.',
    'Tạo hình móng, chăm sóc cuticle, đánh bóng và sơn thường — gọn gàng tự nhiên.',
    'Kynnen muotoilu, kynsinhoidon hoito, kiillotus ja klassinen lakkaus.',
    45, 40.0, 40,
    'Phổ biến', 'auto_awesome', '/static/images/services/classic-manicure.png', 1
),

-- 2. Gel Manicure
(
    1,
    'Gel Manicure',
    'Làm móng gel',
    'Gelimanikyyri',
    'Long-lasting gel polish cured under UV/LED light, stays flawless up to 3 weeks.',
    'Sơn gel bền đẹp lên đến 3 tuần, không tróc, bóng đẹp như mới.',
    'Pitkäkestoinen gelilaakaus UV/LED-valolla, kestää jopa 3 viikkoa.',
    60, 45.0, 45,
    'Bán chạy', 'colorize', '/static/images/services/gel-manicure.png', 1
),

-- 3. Spa Manicure
(
    1,
    'Spa Manicure',
    'Làm móng spa',
    'Spa-manikyyri',
    'Luxury hand treatment with exfoliation, moisturizing mask, massage and gel polish.',
    'Tẩy tế bào chết, đắp mặt nạ dưỡng ẩm, massage tay và sơn gel cao cấp.',
    'Luksuskäsihoito kuorinnan, kosteuttavan naamion, hieronnan ja gelilaakauksen kanssa.',
    75, 50.0, 50,
    NULL, 'spa', '/static/images/services/spa-manicure.png', 1
),

-- ------------------------------------------------------------
-- services — Pedicure (category_id = 2)
-- ------------------------------------------------------------

-- 4. Classic Pedicure
(
    2,
    'Classic Pedicure',
    'Chăm sóc móng chân',
    'Peruspedikyyrі',
    'Foot soak, callus removal, nail trimming, cuticle care and moisturizing cream.',
    'Ngâm chân, tẩy da chai, cắt móng, chăm sóc cuticle và thoa kem dưỡng.',
    'Jalkakayla, kovettumien poisto, kynsien leikkaus, kynsinhoidon hoito ja kosteutusvoide.',
    45, 45.0, 45,
    NULL, 'clean_hands', '/static/images/services/classic-pedicure.png', 1
),

-- 5. Gel Pedicure
(
    2,
    'Gel Pedicure',
    'Móng chân gel',
    'Gelipedikyyrі',
    'Full classic pedicure with long-lasting gel polish that stays perfect up to 3 weeks.',
    'Pedicure đầy đủ kết hợp sơn gel bền màu lên đến 3 tuần.',
    'Täydellinen pedikyyrі pitkäkestoisella gelilakauksella, kestää jopa 3 viikkoa.',
    75, 85.0, 85,
    'Phổ biến', 'water_drop', '/static/images/services/gel-pedicure.png', 1
),

-- 6. Spa Pedicure
(
    2,
    'Spa Pedicure',
    'Chăm sóc chân spa',
    'Spa-pedikyyrі',
    'Premium foot spa with exfoliation, massage, callus treatment and gel polish finish.',
    'Trải nghiệm spa chân cao cấp — tẩy da chết, massage, trị chai và sơn gel.',
    'Premium jalkahoito kuorinnan, hieronnan, kovettumahoidon ja gelilaakauksen kanssa.',
    90, 90.0, 90,
    'Cao cấp', 'workspace_premium', '/static/images/services/spa-pedicure.png', 1
),

-- ------------------------------------------------------------
-- services — Nail Art (category_id = 3)
-- ------------------------------------------------------------

-- 7. Basic Nail Art
(
    3,
    'Basic Nail Art',
    'Vẽ móng cơ bản',
    'Perus kynsikoristelu',
    'Hand-painted simple designs, patterns or solid accents on your nails.',
    'Vẽ tay các họa tiết đơn giản, hoa văn hoặc accent nail theo yêu cầu.',
    'Käsinmaalatut yksinkertaiset kuviot tai koristeelliset aksentit kynsille.',
    30, 20.0, 20,
    NULL, 'brush', '/static/images/services/basic-nail-art.png', 1
),

-- 8. Nail Stamping
(
    3,
    'Nail Stamping',
    'Stamping móng',
    'Kynsi-stamppaus',
    'Precision stamping technique for crisp, intricate patterns across all nails.',
    'Kỹ thuật stamping tạo họa tiết sắc nét, đồng đều trên tất cả các móng.',
    'Tarkka stamppaustekniikka teräville, monimutkaisille kuvioille kaikille kynsille.',
    30, 25.0, 25,
    'Mới', 'local_florist', '/static/images/services/nail-stamping.png', 1
),

-- 9. Rhinestone
(
    3,
    'Rhinestone',
    'Đính đá móng',
    'Strassikivet',
    'Crystal rhinestone application for a glamorous sparkling finish on any nail style.',
    'Đính đá pha lê lấp lánh lên móng, sang trọng và nổi bật.',
    'Strassikivien kiinnitys kimaltavaa ja glamouria varten mille tahansa kynsityylille.',
    20, 15.0, 15,
    NULL, 'diamond', '/static/images/services/rhinestone.png', 1
);

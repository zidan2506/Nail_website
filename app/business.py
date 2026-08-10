"""Nguồn duy nhất cho thông tin doanh nghiệp + nội dung tĩnh của website.

Sửa file này rồi redeploy là nội dung trên web đổi theo — không phải đụng vào
template, không phải chạy pybabel.

Ba khối:
  BUSINESS   — dữ liệu tiệm (tên, Y-tunnus, liên hệ, địa chỉ, giờ mở cửa).
  MEMBERSHIP — giá + hệ số điểm + quyền lợi 3 hạng. Đây là NGUỒN CHÍNH:
               lúc app khởi động, sync_membership_tiers() ghi xuống bảng
               membership_tiers để mọi code sẵn có đọc DB vẫn đúng.
               ⚠ Đổi `price` sẽ vô hiệu hoá stripe_price_id cũ (Stripe Price là
               immutable) → nút mua bị khoá đến khi chạy lại:
                   python -m app.database.setup_stripe_prices
  CONTENT    — các đoạn text tĩnh trên web, mỗi khoá đủ 3 ngôn ngữ.

KHÔNG để ở đây những thứ admin sửa được trong /admin: giá dịch vụ, rewards,
điểm thưởng (loyalty_config), carousel, gallery, nhân viên, thông báo.
Đưa vào đây thì mỗi lần redeploy sẽ ghi đè thứ admin vừa chỉnh.
"""

from flask import session

DEFAULT_LANG = "fi"


BUSINESS = {
    "brand_name": "MisaNails",
    # Logo trên navbar tô màu nhấn cho nửa sau của tên, nên cần tách đôi.
    # Ghép lại phải đúng bằng brand_name.
    "brand_logo_parts": ["Misa", "Nails"],

    # Y-tunnus. Bắt buộc hiển thị theo luật Phần Lan khi bán hàng online.
    # ⚠ ĐANG TRỐNG — điền trước khi mở cho khách thật.
    "business_id": "",

    "phone": "+358 465 978 425",
    "email": "dahacaree@gmail.com",

    # Một dòng — dùng cho link Google Maps và sự kiện Google Calendar.
    "address": "Kyyhkysmäki 9, 02650 Espoo",
    # Nhiều dòng — dùng khi hiển thị trên trang.
    "address_lines": ["Kyyhkysmäki 9 A", "02650 Espoo, Finland"],

    "branches": [
        {"name": "MisaNails Espoo", "address": "Kyyhkysmäki 9 A, 02650 Espoo"},
    ],

    # Phải khớp BUSINESS_OPEN / BUSINESS_CLOSE trong services/booking_service.py,
    # nếu không khách đọc giờ trên web rồi mở wizard sẽ không thấy slot tương ứng.
    "hours": {"open": "09:00", "close": "18:00"},

    # Ưu đãi cho khách đăng ký lần đầu, hiện trên banner trang chủ.
    "first_visit_discount_pct": 15,

    # Số liệu quảng cáo. ⚠ CHƯA ĐƯỢC XÁC THỰC — chỉnh cho đúng thực tế trước
    # khi mở cho khách. Lưu ý hai bộ này đang tự mâu thuẫn: trang chủ ghi 5K+
    # khách còn trang About ghi 12k+; trang chủ ghi 10+ thợ còn About đếm số
    # nhân viên thật trong DB (hiện là 1).
    "home_stats": {"clients": "5K+", "safe_products": "100%", "artists": "10+"},
    "about_stats": {"years": "5+", "clients": "12k+", "rating": "4.9"},
}


MEMBERSHIP = {
    "Silver": {
        "price": 0.00,
        "point_multiplier": 1.0,
        "duration_days": 365,
        "perks": [
            {
                "en": "Earn base loyalty points on every visit",
                "fi": "Ansaitse peruskanta-asiakaspisteitä joka käynnillä",
                "vi": "Nhận điểm thưởng cơ bản mỗi lần ghé",
            },
            {
                "en": "Birthday bonus points",
                "fi": "Syntymäpäivän bonuspisteet",
                "vi": "Điểm thưởng sinh nhật",
            },
            {
                "en": "Access to member-only promotions",
                "fi": "Pääsy vain jäsenille tarkoitettuihin tarjouksiin",
                "vi": "Truy cập ưu đãi dành riêng cho thành viên",
            },
            {
                "en": "Monthly reward voucher",
                "fi": "Kuukausittainen palkintokuponki",
                "vi": "Voucher thưởng hàng tháng",
            },
            {
                "en": "Priority booking (standard)",
                "fi": "Etusijavaraus (perus)",
                "vi": "Đặt lịch ưu tiên (tiêu chuẩn)",
            },
        ],
    },
    "Gold": {
        "price": 49.99,
        "point_multiplier": 1.5,
        "duration_days": 365,
        "perks": [
            {
                "en": "Everything in Silver",
                "fi": "Kaikki Silverissä",
                "vi": "Mọi thứ trong Silver",
            },
            {
                "en": "Early access to new services & seasonal offers",
                "fi": "Ennakkopääsy uusiin palveluihin ja kausitarjouksiin",
                "vi": "Truy cập sớm dịch vụ mới & ưu đãi theo mùa",
            },
            {
                "en": "Complimentary nail care kit (quarterly)",
                "fi": "Maksuton kynsienhoitosetti (neljännesvuosittain)",
                "vi": "Bộ chăm sóc móng miễn phí (hàng quý)",
            },
            {
                "en": "Dedicated booking slot on weekends",
                "fi": "Oma varausaika viikonloppuisin",
                "vi": "Khung giờ đặt riêng cuối tuần",
            },
        ],
    },
    "Diamond": {
        "price": 99.99,
        "point_multiplier": 2.0,
        "duration_days": 365,
        "perks": [
            {
                "en": "Everything in Gold",
                "fi": "Kaikki Goldissa",
                "vi": "Mọi thứ trong Gold",
            },
            {
                "en": "Free add-on service every visit",
                "fi": "Ilmainen lisäpalvelu joka käynnillä",
                "vi": "Dịch vụ bổ sung miễn phí mỗi lần ghé",
            },
            {
                "en": "Personal nail stylist assignment",
                "fi": "Oma henkilökohtainen kynsistylisti",
                "vi": "Chỉ định thợ móng riêng",
            },
            {
                "en": "VIP lounge access & complimentary drinks",
                "fi": "Pääsy VIP-loungeen ja maksuttomat juomat",
                "vi": "Vào phòng chờ VIP & đồ uống miễn phí",
            },
        ],
    },
}


CONTENT = {
    "home.why_1_desc": {
        "en": "Trusted by thousands of satisfied customers who love our work.",
        "fi": "Tuhannet tyytyväiset asiakkaat luottavat työhömme.",
        "vi": "Được hàng nghìn khách hàng hài lòng yêu thích tin tưởng.",
    },
    "home.why_2_desc": {
        "en": "We use only premium, non-toxic products for your health and safety.",
        "fi": "Käytämme vain premium-luokan myrkyttömiä tuotteita terveytesi ja turvallisuutesi vuoksi.",
        "vi": "Chúng tôi chỉ dùng sản phẩm cao cấp, không độc hại vì sức khỏe và an toàn của bạn.",
    },
    "home.why_3_desc": {
        "en": "Our highly trained professionals bring your vision to life.",
        "fi": "Osaavat ammattilaisemme herättävät visiosi eloon.",
        "vi": "Đội ngũ chuyên gia lành nghề biến ý tưởng của bạn thành hiện thực.",
    },
    "home.testimonial_1_quote": {
        "en": "\"Absolutely wonderful experience! The attention to detail is unmatched, and my nails have never looked better. Highly recommend the gel extensions.\"",
        "fi": "\"Aivan ihana kokemus! Yksityiskohtien huomiointi on vertaansa vailla, eivätkä kynteni ole koskaan näyttäneet paremmilta. Suosittelen lämpimästi geelipidennyksiä.\"",
        "vi": "\"Trải nghiệm tuyệt vời! Sự tỉ mỉ đến từng chi tiết không đâu sánh bằng, và móng của tôi chưa bao giờ đẹp đến thế. Rất khuyến khích dịch vụ nối móng gel.\"",
    },
    "home.testimonial_1_name": {
        "en": "Sarah Jenkins",
        "fi": "Sarah Jenkins",
        "vi": "Sarah Jenkins",
    },
    "home.testimonial_1_role": {
        "en": "Gold member",
        "fi": "Kulta-jäsen",
        "vi": "Thành viên Vàng",
    },
    "home.testimonial_2_quote": {
        "en": "\"The ambiance is so relaxing, and the staff is incredibly professional. I love the creative nail art options they offer. A true luxury experience.\"",
        "fi": "\"Tunnelma on niin rentouttava ja henkilökunta uskomattoman ammattitaitoista. Rakastan heidän luovia kynsitaidevaihtoehtojaan. Aito ylellisyyskokemus.\"",
        "vi": "\"Không gian thật thư giãn, và nhân viên vô cùng chuyên nghiệp. Tôi thích những lựa chọn nghệ thuật móng sáng tạo của họ. Một trải nghiệm sang trọng đích thực.\"",
    },
    "home.testimonial_2_name": {
        "en": "Maria Rodriguez",
        "fi": "Maria Rodriguez",
        "vi": "Maria Rodriguez",
    },
    "home.testimonial_2_role": {
        "en": "First-time client",
        "fi": "Ensikertalainen",
        "vi": "Khách hàng lần đầu",
    },
    "home.promo_title": {
        "en": "Create an account & get %(pct)s%% off your first visit",
        "fi": "Luo tili ja saat %(pct)s %% alennuksen ensimmäisestä käynnistäsi",
        "vi": "Tạo tài khoản & giảm %(pct)s%% cho lần ghé thăm đầu tiên",
    },
    "home.promo_sub": {
        "en": "Join our community today and start enjoying the perks of premium nail care right away.",
        "fi": "Liity yhteisöömme tänään ja ala nauttia premium-kynsihoidon eduista heti.",
        "vi": "Tham gia cộng đồng của chúng tôi hôm nay và bắt đầu tận hưởng ưu đãi chăm sóc móng cao cấp ngay lập tức.",
    },
    "about.hero_sub": {
        "en": "Redefining luxury wellness with precise, artisanal care in a sanctuary of soft mood and quiet elegance.",
        "fi": "Määrittelemme ylellisen hyvinvoinnin uudelleen tarkalla, käsityöläismäisellä hoidolla pehmeän tunnelman ja hillityn eleganssin keitaassa.",
        "vi": "Định nghĩa lại sự chăm sóc sang trọng bằng liệu trình tỉ mỉ, thủ công trong một không gian nhẹ nhàng và thanh lịch.",
    },
    "about.story_lead": {
        "en": "At %(brand)s, we believe that true luxury lies in the details. Founded on the principle of bringing atelier-level precision to daily wellness, our space was designed as a retreat from the noise of the city.",
        # fi: bản cũ viết "DahaCaressa" (sijamuoto). Tên mới ghép sẵn nên câu
        # được viết lại ở chủ cách để không phải chia biến cách theo tên.
        "fi": "%(brand)s uskoo, että todellinen ylellisyys piilee yksityiskohdissa. Periaatteenamme on tuoda ateljee-tason tarkkuus päivittäiseen hyvinvointiin, ja tilamme on suunniteltu pakopaikaksi kaupungin melulta.",
        "vi": "Tại %(brand)s, chúng tôi tin rằng sự sang trọng thực sự nằm ở từng chi tiết. Được xây dựng trên nguyên tắc mang sự tỉ mỉ đẳng cấp atelier vào việc chăm sóc hằng ngày, không gian của chúng tôi được thiết kế như một chốn nghỉ ngơi khỏi sự ồn ào của phố thị.",
    },
    "about.story_body": {
        "en": "Every treatment is a careful composition of quality products, rigorous hygiene standards, and the trained hands of our artists. We don't just provide a service; we curate an experience that honors your time and elevates your personal care ritual.",
        "fi": "Jokainen hoito on huolellinen yhdistelmä laadukkaita tuotteita, tiukkoja hygieniastandardeja ja artistiemme koulutettuja käsiä. Emme vain tarjoa palvelua; luomme kokemuksen, joka kunnioittaa aikaasi ja nostaa henkilökohtaisen hoitorituaalisi uudelle tasolle.",
        "vi": "Mỗi liệu trình là sự kết hợp cẩn thận giữa sản phẩm chất lượng, tiêu chuẩn vệ sinh nghiêm ngặt và đôi tay lành nghề của các nghệ nhân. Chúng tôi không chỉ cung cấp dịch vụ; chúng tôi tạo nên trải nghiệm tôn trọng thời gian của bạn và nâng tầm nghi thức chăm sóc bản thân.",
    },
    "about.value_hygiene_desc": {
        "en": "Medical-grade sterilization processes for every tool, ensuring your safety is never compromised.",
        "fi": "Lääketieteellisen tason sterilointi jokaiselle työkalulle takaa, ettei turvallisuudestasi tingitä koskaan.",
        "vi": "Quy trình tiệt trùng đạt chuẩn y tế cho mọi dụng cụ, đảm bảo an toàn của bạn không bao giờ bị đánh đổi.",
    },
    "about.value_artists_desc": {
        "en": "Continuous education and mastery of techniques mean you receive the pinnacle of modern care.",
        "fi": "Jatkuva kouluttautuminen ja tekniikoiden hallinta takaavat, että saat modernin hoidon huipun.",
        "vi": "Việc học hỏi liên tục và tinh thông kỹ thuật đảm bảo bạn nhận được sự chăm sóc hiện đại đỉnh cao.",
    },
    "about.value_quality_desc": {
        "en": "We source only premium, non-toxic, and sustainable materials for long-lasting, brilliant results.",
        "fi": "Käytämme vain premium-luokan, myrkyttömiä ja kestäviä materiaaleja pitkäkestoisiin, upeisiin tuloksiin.",
        "vi": "Chúng tôi chỉ chọn vật liệu cao cấp, không độc hại và bền vững để mang lại kết quả rực rỡ, lâu dài.",
    },
    "about.value_care_desc": {
        "en": "Your comfort is our priority. Enjoy a serene environment designed entirely around your relaxation.",
        "fi": "Mukavuutesi on prioriteettimme. Nauti rauhallisesta ympäristöstä, joka on suunniteltu täysin rentoutumistasi varten.",
        "vi": "Sự thoải mái của bạn là ưu tiên của chúng tôi. Hãy tận hưởng không gian yên tĩnh được thiết kế hoàn toàn cho sự thư giãn của bạn.",
    },
    "about.cta_sub": {
        "en": "Experience the %(brand)s difference in person.",
        # fi: bản cũ là genetiivi "DahaCaren"; đổi sang dạng ghép có gạch nối,
        # cách chuẩn để gắn danh từ riêng nước ngoài mà không chia biến cách.
        "fi": "Koe %(brand)s-ero paikan päällä.",
        "vi": "Trải nghiệm sự khác biệt %(brand)s trực tiếp.",
    },
    "services.hero_sub": {
        "en": "Discover a curated collection of premium nail care and aesthetic treatments designed for the modern individual. Precision meets tranquility in every session.",
        "fi": "Tutustu valikoituun kokoelmaan premium-kynsihoitoja ja esteettisiä hoitoja, jotka on suunniteltu modernille yksilölle. Tarkkuus ja rauha kohtaavat jokaisella kerralla.",
        "vi": "Khám phá bộ sưu tập chọn lọc các liệu trình chăm sóc móng và làm đẹp cao cấp dành cho người hiện đại. Sự tỉ mỉ hòa quyện cùng sự thư thái trong mỗi buổi hẹn.",
    },
    "gallery.hero_sub": {
        "en": "A glimpse into the artistry and precision behind every visit.",
        "fi": "Katsaus jokaisen käynnin taiteeseen ja tarkkuuteen.",
        "vi": "Thoáng nhìn nghệ thuật và sự tỉ mỉ trong mỗi lần ghé thăm.",
    },
    "success.head_sub_confirmed": {
        "en": "We've reserved your spot. Get ready for some well-deserved pampering.",
        "fi": "Olemme varanneet paikkasi. Valmistaudu ansaittuun hemmotteluun.",
        "vi": "Chúng tôi đã giữ chỗ cho bạn. Hãy sẵn sàng cho giây phút chăm sóc xứng đáng.",
    },
    "success.head_sub_pending": {
        "en": "We've got your request. We'll email you as soon as the salon confirms your appointment.",
        "fi": "Olemme saaneet pyyntösi. Lähetämme sähköpostin heti kun salonki vahvistaa aikasi.",
        "vi": "Chúng tôi đã nhận yêu cầu của bạn. Bạn sẽ nhận được email ngay khi salon xác nhận lịch hẹn.",
    },
    "success.note_response_time": {
        "en": "Usually within a few hours during opening times.",
        "fi": "Yleensä muutamassa tunnissa aukioloaikoina.",
        "vi": "Thường trong vài giờ, vào khung giờ mở cửa.",
    },
    "success.note_arrive_early": {
        "en": "Arrive 5-10 minutes early to pick your shade.",
        "fi": "Saavu 5-10 minuuttia etuajassa valitsemaan sävysi.",
        "vi": "Đến sớm 5-10 phút để chọn màu ưng ý.",
    },
    "success.invite_signup": {
        "en": "Create an account to track your loyalty points, reschedule appointments, and save your favorite colors.",
        "fi": "Luo tili seurataksesi kanta-asiakaspisteitäsi, siirtääksesi aikoja ja tallentaaksesi suosikkivärisi.",
        "vi": "Tạo tài khoản để theo dõi điểm thưởng, đổi lịch hẹn và lưu những màu yêu thích của bạn.",
    },
    "booking.step_service_sub": {
        "en": "Choose from our curated selection of luxury treatments.",
        "fi": "Valitse valikoiduista ylellisyyshoidoistamme.",
        "vi": "Lựa chọn từ bộ sưu tập liệu trình cao cấp của chúng tôi.",
    },
    "booking.step_staff_sub": {
        "en": "Select your preferred stylist or let us match you.",
        "fi": "Valitse haluamasi stylisti tai anna meidän valita puolestasi.",
        "vi": "Chọn thợ bạn thích hoặc để chúng tôi ghép cho bạn.",
    },
    "booking.step_contact_sub": {
        "en": "Please provide your contact information to secure the booking.",
        "fi": "Anna yhteystietosi varmistaaksesi varauksen.",
        "vi": "Vui lòng cung cấp thông tin liên hệ để xác nhận đặt lịch.",
    },
    "booking.email_note_before": {
        "en": "You'll receive a verification email after confirming. Your booking will be",
        "fi": "Saat vahvistussähköpostin vahvistuksen jälkeen. Varauksesi on",
        "vi": "Bạn sẽ nhận email xác minh sau khi xác nhận. Lịch đặt của bạn sẽ ở trạng thái",
    },
    "booking.email_note_after": {
        "en": "until the salon confirms your appointment.",
        "fi": "kunnes salonki vahvistaa aikasi.",
        "vi": "cho đến khi salon xác nhận lịch hẹn của bạn.",
    },
    "booking.signin_hint": {
        "en": "Sign in to earn loyalty points with this booking.",
        "fi": "Kirjaudu sisään ansaitaksesi kanta-asiakaspisteitä tästä varauksesta.",
        "vi": "Đăng nhập để tích điểm thưởng cho lần đặt này.",
    },
    "booking.cancel_policy": {
        "en": "By confirming, you agree to our 24h cancellation policy.",
        "fi": "Vahvistamalla hyväksyt 24 tunnin peruutusehtomme.",
        "vi": "Bằng việc xác nhận, bạn đồng ý với chính sách hủy trong 24 giờ.",
    },
    "reschedule.sub": {
        "en": "Modify your session with ease. Please note our 24-hour rescheduling window to ensure we can accommodate all guests.",
        "fi": "Muuta aikaasi vaivattomasti. Huomaathan 24 tunnin muutosaikamme, jotta voimme palvella kaikkia asiakkaita.",
        "vi": "Đổi buổi hẹn của bạn dễ dàng. Vui lòng lưu ý khung 24 giờ để đổi lịch nhằm đảm bảo phục vụ mọi khách hàng.",
    },
    "reschedule.policy": {
        "en": "Bookings can only be rescheduled at least 24 hours in advance and can only be changed once. Further changes may require a new deposit.",
        "fi": "Varauksia voi siirtää vain vähintään 24 tuntia etukäteen ja vain kerran. Lisämuutokset voivat vaatia uuden ennakkomaksun.",
        "vi": "Lịch chỉ có thể đổi trước ít nhất 24 giờ và chỉ đổi được một lần. Thay đổi thêm có thể cần đặt cọc mới.",
    },
    "membership.intro_sub": {
        "en": "Unlock exclusive perks, rewards, and priority care tailored to your loyalty.",
        "fi": "Avaa eksklusiiviset edut, palkinnot ja etusijainen hoito uskollisuutesi mukaan.",
        "vi": "Mở khóa đặc quyền, phần thưởng và ưu tiên chăm sóc riêng cho sự gắn bó của bạn.",
    },
    "auth.verify_sub": {
        "en": "Just one more step to secure your account and unlock your personalized beauty journey.",
        "fi": "Enää yksi askel: suojaa tilisi ja avaa oma kauneuspolkusi.",
        "vi": "Chỉ còn một bước nữa để bảo vệ tài khoản và mở khoá hành trình làm đẹp của bạn.",
    },
    "loyalty.voucher_active": {
        "en": "Show this code to our staff at your next visit to redeem.",
        "fi": "Näytä tämä koodi henkilökunnallemme seuraavalla käynnilläsi lunastaaksesi sen.",
        "vi": "Xuất trình mã này cho nhân viên trong lần ghé tiếp theo để đổi.",
    },
    "loyalty.voucher_expired": {
        "en": "This voucher has expired and is no longer valid.",
        "fi": "Tämä kuponki on vanhentunut eikä ole enää voimassa.",
        "vi": "Voucher này đã hết hạn và không còn hiệu lực.",
    },
    "email.verify_register_subject": {
        "en": "Verify your email – %(brand)s",
        "fi": "Verify your email – %(brand)s",
        "vi": "Xác minh email của bạn – %(brand)s",
    },
    "email.verify_password_change_subject": {
        "en": "Password Change Request – %(brand)s",
        "fi": "Password Change Request – %(brand)s",
        "vi": "Yêu cầu đổi mật khẩu – %(brand)s",
    },
    "email.verify_email_change_subject": {
        "en": "Email Change Request – %(brand)s",
        "fi": "Email Change Request – %(brand)s",
        "vi": "Yêu cầu đổi email – %(brand)s",
    },
    "email.verify_forgot_password_subject": {
        "en": "Reset Your Password – %(brand)s",
        "fi": "Reset Your Password – %(brand)s",
        "vi": "Đặt lại mật khẩu – %(brand)s",
    },
    "email.verify_booking_subject": {
        "en": "Your Booking Verification Code – %(brand)s",
        "fi": "Your Booking Verification Code – %(brand)s",
        "vi": "Mã xác nhận đặt lịch của bạn – %(brand)s",
    },
    "email.thank_you_subject": {
        "en": "Your booking request has been received",
        "fi": "Your booking request has been received",
        "vi": "Chúng tôi đã nhận được yêu cầu đặt lịch của bạn",
    },
    "email.verify_register_body": {
        "en": "Hello,\n\nYour verification code is: %(code)s\n\nPlease enter this code to confirm your email address and complete your registration.\n\nIf you did not create an account with %(brand)s, please ignore this email.\n",
        "fi": "Hello,\n\nYour verification code is: %(code)s\n\nPlease enter this code to confirm your email address and complete your registration.\n\nIf you did not create an account with %(brand)s, please ignore this email.\n",
        "vi": "Xin chào,\n\nMã xác minh của bạn là: %(code)s\n\nVui lòng nhập mã này để xác nhận địa chỉ email và hoàn tất đăng ký.\n\nNếu bạn không tạo tài khoản tại %(brand)s, vui lòng bỏ qua email này.\n",
    },
    "email.verify_password_change_body": {
        "en": "Hello,\n\nYour verification code is: %(code)s\n\nPlease enter this code to confirm your password change request.\n\nIf you did not request this, please ignore this email and your password will remain unchanged.\n",
        "fi": "Hello,\n\nYour verification code is: %(code)s\n\nPlease enter this code to confirm your password change request.\n\nIf you did not request this, please ignore this email and your password will remain unchanged.\n",
        "vi": "Xin chào,\n\nMã xác minh của bạn là: %(code)s\n\nVui lòng nhập mã này để xác nhận yêu cầu đổi mật khẩu.\n\nNếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email và mật khẩu của bạn sẽ được giữ nguyên.\n",
    },
    "email.verify_email_change_body": {
        "en": "Hello,\n\nYour verification code is: %(code)s\n\nPlease enter this code to confirm your email address change request.\n\nIf you did not request this, please ignore this email and your email address will remain unchanged.\n",
        "fi": "Hello,\n\nYour verification code is: %(code)s\n\nPlease enter this code to confirm your email address change request.\n\nIf you did not request this, please ignore this email and your email address will remain unchanged.\n",
        "vi": "Xin chào,\n\nMã xác minh của bạn là: %(code)s\n\nVui lòng nhập mã này để xác nhận yêu cầu đổi địa chỉ email.\n\nNếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email và địa chỉ email của bạn sẽ được giữ nguyên.\n",
    },
    "email.verify_forgot_password_body": {
        "en": "Hello,\n\nYour password reset code is: %(code)s\n\nPlease enter this code to reset your password. This code expires in 10 minutes.\n\nIf you did not request a password reset, please ignore this email.\n",
        "fi": "Hello,\n\nYour password reset code is: %(code)s\n\nPlease enter this code to reset your password. This code expires in 10 minutes.\n\nIf you did not request a password reset, please ignore this email.\n",
        "vi": "Xin chào,\n\nMã đặt lại mật khẩu của bạn là: %(code)s\n\nVui lòng nhập mã này để đặt lại mật khẩu. Mã sẽ hết hạn sau 10 phút.\n\nNếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.\n",
    },
    "email.verify_booking_body": {
        "en": "Hello,\n\nYour verification code is: %(code)s\n\nPlease enter this code on the verification page to confirm your booking.\n\nIf you did not request this, please ignore this email.\n",
        "fi": "Hello,\n\nYour verification code is: %(code)s\n\nPlease enter this code on the verification page to confirm your booking.\n\nIf you did not request this, please ignore this email.\n",
        "vi": "Xin chào,\n\nMã xác minh của bạn là: %(code)s\n\nVui lòng nhập mã này trên trang xác minh để xác nhận đặt lịch.\n\nNếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email này.\n",
    },
    "email.thank_you_body": {
        "en": "Hi %(name)s,\n\nThank you for your booking.\n\nWe have received your booking request and it is currently pending confirmation.\n\nBooking details:\n- Service: %(service)s\n- Staff: %(staff)s\n- Date: %(date)s\n- Time: %(start)s - %(end)s\n\nWe will contact you again once your booking has been confirmed.\n\nBest regards,\n%(brand)s\n",
        "fi": "Hi %(name)s,\n\nThank you for your booking.\n\nWe have received your booking request and it is currently pending confirmation.\n\nBooking details:\n- Service: %(service)s\n- Staff: %(staff)s\n- Date: %(date)s\n- Time: %(start)s - %(end)s\n\nWe will contact you again once your booking has been confirmed.\n\nBest regards,\n%(brand)s\n",
        "vi": "Xin chào %(name)s,\n\nCảm ơn bạn đã đặt lịch.\n\nChúng tôi đã nhận được yêu cầu đặt lịch của bạn và hiện đang chờ xác nhận.\n\nChi tiết đặt lịch:\n- Dịch vụ: %(service)s\n- Nhân viên: %(staff)s\n- Ngày: %(date)s\n- Giờ: %(start)s - %(end)s\n\nChúng tôi sẽ liên hệ lại khi đặt lịch của bạn được xác nhận.\n\nTrân trọng,\n%(brand)s\n",
    },
}


def txt(key, **kw):
    """Trả đoạn text của `key` theo ngôn ngữ đang chọn, fallback về 'en'.

    Có kwargs thì nội suy kiểu %(name)s — dùng cho nội dung email và các câu
    chèn số liệu. Không kwargs thì trả nguyên chuỗi, nên '%%' trong CONTENT
    chỉ được viết ở những khoá thật sự có nội suy.
    """
    entry = CONTENT.get(key)
    if entry is None:
        return ""
    s = entry.get(session.get("lang") or DEFAULT_LANG) or entry.get("en", "")
    return s % kw if kw else s


def perks(tier_name):
    """Danh sách quyền lợi của một hạng, đã chọn đúng ngôn ngữ."""
    tier = MEMBERSHIP.get(tier_name)
    if not tier:
        return []
    lang = session.get("lang") or DEFAULT_LANG
    return [p.get(lang) or p["en"] for p in tier["perks"]]

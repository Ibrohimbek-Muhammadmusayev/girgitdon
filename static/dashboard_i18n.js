// Dashboard Ko'p tilli lug'at
const dashboardTranslations = {
    uz: {
        dashboard_title: "Girgitdon Boshqaruv",
        nav_dashboard: "Asosiy Dashbord",
        nav_menu: "Taomlar & Menyu",
        nav_tables: "Stollar & QR Kodlar",
        nav_cashier: "Kassa & To'lovlar",
        nav_kitchen: "Oshxona (KDS)",
        nav_history: "Buyurtmalar Tarixi",
        nav_visitors: "Mehmonlar & Qurilmalar",
        nav_settings: "Sozlamalar",
        check_menu: "Menyuni tekshirish",
        admin_role: "Restoran Administratori",
        kitchen_screen: "Oshxona ekrani",
        filter: "Filtrlash",
        search: "Qidiruv",
        all: "Hammasi",
        save: "Saqlash",
        edit: "Tahrirlash",
        delete: "O'chirish",
        close: "Yopish",
        details: "Ko'rish",
        orders: "Buyurtmalar",
        table: "stol",
        total_revenue: "Jami Tushum",
        today_revenue: "Bugungi daromad",
        completed: "Yakunlandi",
        cooking: "Tayyorlanmoqda",
        ready: "Tayyor",
        pending: "Kutilmoqda",
        cancelled: "Bekor qilindi",
        som: "so'm"
    },
    oz: {
        dashboard_title: "Гиргитдон Бошқарув",
        nav_dashboard: "Асосий Дашборд",
        nav_menu: "Таомлар & Меню",
        nav_tables: "Столлар & QR Кодлар",
        nav_cashier: "Касса & Тўловлар",
        nav_kitchen: "Ошхона (KDS)",
        nav_history: "Буюртмалар Тарихи",
        nav_visitors: "Меҳмонлар & Қурилмалар",
        nav_settings: "Созламалар",
        check_menu: "Менюни текшириш",
        admin_role: "Ресторан Администратори",
        kitchen_screen: "Ошхона экрани",
        filter: "Филтрлаш",
        search: "Қидирув",
        all: "Ҳаммаси",
        save: "Сақлаш",
        edit: "Таҳрирлаш",
        delete: "Ўчириш",
        close: "Ёпиш",
        details: "Кўриш",
        orders: "Буюртмалар",
        table: "-стол",
        total_revenue: "Жами Тушум",
        today_revenue: "Бугунги даромад",
        completed: "Якунланди",
        cooking: "Тайёрланмоқда",
        ready: "Тайёр",
        pending: "Кутилмоқда",
        cancelled: "Бекор қилинди",
        som: "сўм"
    },
    ru: {
        dashboard_title: "Girgitdon Панель",
        nav_dashboard: "Главная Панель",
        nav_menu: "Блюда и Меню",
        nav_tables: "Столы и QR-коды",
        nav_cashier: "Касса и Оплата",
        nav_kitchen: "Кухня (KDS)",
        nav_history: "История Заказов",
        nav_visitors: "Гости и Устройства",
        nav_settings: "Настройки",
        check_menu: "Просмотр меню",
        admin_role: "Администратор ресторана",
        kitchen_screen: "Экран кухни",
        filter: "Фильтр",
        search: "Поиск",
        all: "Все",
        save: "Сохранить",
        edit: "Редактировать",
        delete: "Удалить",
        close: "Закрыть",
        details: "Просмотр",
        orders: "Заказы",
        table: "стол",
        total_revenue: "Общая выручка",
        today_revenue: "Выручка за сегодня",
        completed: "Выполнен",
        cooking: "Готовится",
        ready: "Готово",
        pending: "В ожидании",
        cancelled: "Отменен",
        som: "сум"
    },
    en: {
        dashboard_title: "Girgitdon Admin",
        nav_dashboard: "Dashboard",
        nav_menu: "Dishes & Menu",
        nav_tables: "Tables & QR Codes",
        nav_cashier: "Cashier & POS",
        nav_kitchen: "Kitchen (KDS)",
        nav_history: "Order History",
        nav_visitors: "Guests & Devices",
        nav_settings: "Settings",
        check_menu: "View live menu",
        admin_role: "Restaurant Admin",
        kitchen_screen: "Kitchen display",
        filter: "Filter",
        search: "Search",
        all: "All",
        save: "Save",
        edit: "Edit",
        delete: "Delete",
        close: "Close",
        details: "Details",
        orders: "Orders",
        table: "table",
        total_revenue: "Total Revenue",
        today_revenue: "Today's Revenue",
        completed: "Completed",
        cooking: "Cooking",
        ready: "Ready",
        pending: "Pending",
        cancelled: "Cancelled",
        som: "UZS"
    }
};

function setDashboardLanguage(lang) {
    localStorage.setItem('girgitdon_dashboard_lang', lang);
    applyDashboardLanguage(lang);
}

function applyDashboardLanguage(lang = 'uz') {
    const t = dashboardTranslations[lang] || dashboardTranslations.uz;
    
    document.querySelectorAll('[data-d-i18n]').forEach(el => {
        const key = el.getAttribute('data-d-i18n');
        if (t[key]) {
            el.innerText = t[key];
        }
    });

    // Language pills active state
    document.querySelectorAll('.dash-lang-btn').forEach(btn => {
        if (btn.getAttribute('data-lang') === lang) {
            btn.classList.add('bg-orange-500', 'text-white', 'shadow-sm');
            btn.classList.remove('text-slate-600', 'hover:bg-slate-100');
        } else {
            btn.classList.remove('bg-orange-500', 'text-white', 'shadow-sm');
            btn.classList.add('text-slate-600', 'hover:bg-slate-100');
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('girgitdon_dashboard_lang') || 'uz';
    applyDashboardLanguage(saved);
});

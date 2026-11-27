// 桌面端可执行入口（release 下隐藏控制台窗口）
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    yuezangjing_desktop_lib::run()
}

/**
 * 用于调试器截图：这个文件可以正常编译运行。
 */
public class DebugCheck {

    public static void main(String[] args) {
        int total = 0;
        for (int i = 0; i < 5; i++) {
            total += i; // 断点设这里
        }
        System.out.println(total);
    }
}

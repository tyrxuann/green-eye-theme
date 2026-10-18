/**
 * 用于调试器和参数名 inlay hint 截图：这个文件可以正常编译运行。
 */
public class DebugCheck {

    static int combine(int left, int right) {
        return left + right;
    }

    public static void main(String[] args) {
        int total = 0;
        for (int i = 0; i < 5; i++) {
            total += i; // 断点设这里
        }
        int combined = combine(1, 2); // 参数名 hint：left / right
        System.out.println(total + combined);
    }
}

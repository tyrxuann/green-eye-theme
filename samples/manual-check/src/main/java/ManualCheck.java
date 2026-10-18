import java.util.Arrays;
import java.util.List;

/**
 * Green Eye 真机检查样例。
 */
public class ManualCheck {

    /**
     * @param values 输入值
     * @return 求和结果
     */
    public static int sum(List<Integer> values) {
        int total = 0;
        for (int value : values) {
            total += value;
        }
        return total;
    }

    @Override
    public String toString() {
        return "ManualCheck";
    }

    @Deprecated
    static void oldApi() {
    }

    /**
     * @param args 忽略
     */
    public static void main(String[] args) {
        int unused = 42;             // 黄色警告
        List<Integer> values = Arrays.asList(1, 2, 3);
        int result = sum(values);    // 断点设这里；参数名 inlay hint
        oldApi();                    // 删除线
        System.out.println(result);
        // TODO: 截图这一行
    }
}

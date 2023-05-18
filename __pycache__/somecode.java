
interface A{
    public abstract double mA(double d);
}

interface B{
    public abstract void mB(int i);
}

interface C extends A,B{
    public final double KC = 3.5;
    public static void mC(){
        System.out.println("I am from C");
    }
}

class Y implements C{

    public double mA(double d){
        return d*2;
    }

    public void mB(int i){
        int value = i+this.KC;
        System.out.println("mB.i = "+value);
    }

    public static void main(String[] args){
        double a = this.mA(4.5);
        this.mB(8);
        mC();
    }
}
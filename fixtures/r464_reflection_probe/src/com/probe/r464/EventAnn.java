package com.probe.r464;

import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

@Retention(RetentionPolicy.RUNTIME)
public @interface EventAnn {
    String name();
    int priority() default 0;
}

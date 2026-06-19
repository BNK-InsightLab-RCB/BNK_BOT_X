package org.bnkbotxapi.bnkbotxapi.common.exception;

import org.springframework.http.HttpStatus;

import java.util.function.Supplier;

public enum CommonExceptions {
    BAD_AUTH(() -> new CommonTaskException(HttpStatus.UNAUTHORIZED, "BAD_AUTH", "Invalid login information")),
    FORBIDDEN(() -> new CommonTaskException(HttpStatus.FORBIDDEN, "FORBIDDEN", "Forbidden")),
    ENGINE_ERROR(() -> new CommonTaskException(HttpStatus.BAD_GATEWAY, "ENGINE_ERROR", "Chatbot engine request failed"));

    private final Supplier<CommonTaskException> supplier;

    CommonExceptions(Supplier<CommonTaskException> supplier) {
        this.supplier = supplier;
    }

    public CommonTaskException get() {
        return supplier.get();
    }
}

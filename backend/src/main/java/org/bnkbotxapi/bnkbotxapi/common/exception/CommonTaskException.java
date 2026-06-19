package org.bnkbotxapi.bnkbotxapi.common.exception;

import lombok.Getter;
import org.springframework.http.HttpStatus;

@Getter
public class CommonTaskException extends RuntimeException {

    private final HttpStatus status;
    private final String code;

    public CommonTaskException(HttpStatus status, String code, String message) {
        super(message);
        this.status = status;
        this.code = code;
    }
}
